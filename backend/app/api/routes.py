from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import shutil
import uuid
import pandas as pd

from backend.app.database.connection import get_session
from backend.app.database.models import User, Customer, Ticket, Order, AuditLog, AnalyticsMetric, CustomerMemory
from backend.app.api.auth import verify_password, get_password_hash, create_access_token, get_current_user, check_admin_role
from backend.app.agents.agent_graph import agent_graph
from backend.app.rag.pipeline import ingest_pdf
from backend.app.memory.memory_manager import memory_manager

router = APIRouter()

# ----------------- AUTHENTICATION -----------------
@router.post("/auth/register")
def register(email: str = Form(...), password: str = Form(...), role: str = Form("Agent"), db: Session = Depends(get_session)):
    statement = select(User).where(User.email == email)
    existing_user = db.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pwd = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pwd, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "email": user.email, "role": user.role}

@router.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    statement = select(User).where(User.email == form_data.username)
    user = db.exec(statement).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "role": user.role
        }
    }

# ----------------- CUSTOMERS -----------------
@router.get("/customers", response_model=List[Customer])
def list_customers(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    statement = select(Customer)
    return db.exec(statement).all()

@router.get("/customers/{customer_id}")
def get_customer_details(customer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Fetch orders and tickets manually to guarantee full serialization
    stmt_tickets = select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc())
    tickets = db.exec(stmt_tickets).all()
    
    stmt_orders = select(Order).where(Order.customer_id == customer_id).order_by(Order.created_at.desc())
    orders = db.exec(stmt_orders).all()
    
    memories = memory_manager.get_memories(customer_id, db_session=db)
    
    return {
        "customer": customer,
        "tickets": tickets,
        "orders": orders,
        "memories": memories
    }

# ----------------- COPILOT AGENT -----------------
@router.post("/copilot/query")
async def query_copilot(
    customer_id: int = Form(...),
    query: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # Validate customer
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Measure handling duration
    start_time = datetime.utcnow()
    
    # Execute LangGraph workflow
    state_input = {
        "customer_id": customer_id,
        "query": query,
        "chat_history": [],
        "memories": [],
        "context": [],
        "tool_calls": [],
        "tool_outputs": [],
        "response": "",
        "confidence_score": 0.0,
        "escalate": False,
        "category": "General Query",
        "memories_updated": []
    }
    
    try:
        final_state = agent_graph.invoke(state_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")
        
    end_time = datetime.utcnow()
    handling_time_mins = (end_time - start_time).total_seconds() / 60.0
    
    # Store dynamic interaction metric
    sentiment = "Neutral"
    query_lower = query.lower()
    if any(word in query_lower for word in ["angry", "bad", "disappointed", "worst", "fail"]):
        sentiment = "Negative"
    elif any(word in query_lower for word in ["thanks", "good", "great", "awesome", "solved"]):
        sentiment = "Positive"
        
    metric = AnalyticsMetric(
        ticket_id=None, # In-app copilot session
        handling_time=round(handling_time_mins * 60, 2), # log as seconds for precision
        csat_score=None, # to be filled by customer
        sentiment=sentiment,
        category=final_state.get("category", "General Query"),
        timestamp=datetime.utcnow()
    )
    db.add(metric)
    
    # Audit log entry
    log = AuditLog(
        user_id=current_user.id,
        action="COPILOT_QUERY",
        details=f"Agent queried copilot for Customer {customer_id}. Confidence: {final_state.get('confidence_score')}. Escalate: {final_state.get('escalate')}"
    )
    db.add(log)
    db.commit()
    
    return {
        "suggested_reply": final_state.get("response", ""),
        "confidence_score": final_state.get("confidence_score", 0.5),
        "escalate": final_state.get("escalate", False),
        "category": final_state.get("category", "General Query"),
        "memories": final_state.get("memories_updated", []),
        "retrieved_kb": [c["document"] for c in final_state.get("context", [])]
    }

@router.post("/copilot/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_session)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Save PDF locally
    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Ingest PDF into ChromaDB
        chunks_count = ingest_pdf(temp_file_path, source_name=file.filename)
        
        # Log action
        log = AuditLog(
            user_id=current_user.id,
            action="UPLOAD_KB_PDF",
            details=f"Uploaded KB document '{file.filename}'. Generated {chunks_count} vector chunks."
        )
        db.add(log)
        db.commit()
        
        return {
            "filename": file.filename,
            "chunks_ingested": chunks_count,
            "message": "Knowledge base updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# ----------------- MEMORY ENDPOINTS -----------------
@router.get("/copilot/memories/{customer_id}")
def get_customer_memories(customer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    return {
        "customer_id": customer_id,
        "memories": memory_manager.get_memories(customer_id, db_session=db)
    }

@router.delete("/copilot/memories/{customer_id}")
def clear_customer_memories(customer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    memory_manager.delete_memories(customer_id, db_session=db)
    
    log = AuditLog(
        user_id=current_user.id,
        action="CLEAR_MEMORIES",
        details=f"Cleared memories for customer ID {customer_id}"
    )
    db.add(log)
    db.commit()
    return {"message": f"Successfully cleared all memories for customer {customer_id}."}

# ----------------- ANALYTICS -----------------
@router.get("/analytics/dashboard")
def get_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    # Query metrics
    stmt = select(AnalyticsMetric)
    metrics = db.exec(stmt).all()
    
    if not metrics:
        return {
            "avg_handling_time_sec": 0,
            "csat_score": 0.0,
            "resolution_rate": 0.0,
            "sentiment_trends": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "top_categories": {}
        }
        
    df = pd.DataFrame([{
        "handling_time": m.handling_time,
        "csat_score": m.csat_score,
        "sentiment": m.sentiment,
        "category": m.category,
        "timestamp": m.timestamp
    } for m in metrics])
    
    # Calculate stats
    avg_handling = float(df["handling_time"].mean())
    csat = float(df["csat_score"].dropna().mean()) if "csat_score" in df and not df["csat_score"].dropna().empty else 4.2
    
    # Mock resolution rate for visualization dashboard
    res_rate = 92.5
    
    sentiment_counts = df["sentiment"].value_counts().to_dict()
    category_counts = df["category"].value_counts().to_dict()
    
    # Fill missing sentiment classes
    for s in ["Positive", "Neutral", "Negative"]:
        if s not in sentiment_counts:
            sentiment_counts[s] = 0
            
    return {
        "avg_handling_time_sec": round(avg_handling, 2),
        "csat_score": round(csat, 2),
        "resolution_rate": res_rate,
        "sentiment_trends": sentiment_counts,
        "top_categories": category_counts
    }

# ----------------- AUDIT LOGS -----------------
@router.get("/logs", response_model=List[AuditLog])
def get_audit_logs(current_user: User = Depends(check_admin_role), db: Session = Depends(get_session)):
    statement = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    return db.exec(statement).all()
