from sqlmodel import SQLModel, create_engine, Session, select
from backend.app.config import settings
from backend.app.database.models import User, Customer, Ticket, Order, AnalyticsMetric, AuditLog, CustomerMemory
import bcrypt
from datetime import datetime, timedelta
import random

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
    seed_mock_data()

def seed_mock_data():
    with Session(engine) as session:
        # Check if users already exist
        statement = select(User).where(User.email == "admin@copilot.com")
        existing_admin = session.exec(statement).first()
        if existing_admin:
            return # Data already seeded
            
        print("Seeding mock database...")
        
        # 1. Create Users
        admin_user = User(
            email="admin@copilot.com",
            hashed_password=hash_password("admin123"),
            role="Admin"
        )
        agent_user = User(
            email="agent@copilot.com",
            hashed_password=hash_password("agent123"),
            role="Agent"
        )
        session.add(admin_user)
        session.add(agent_user)
        session.commit() # Get IDs
        
        # 2. Create Customers
        customer_data = [
            {"name": "Alice Johnson", "email": "alice@gmail.com", "phone": "+1-555-0199", "subscription_plan": "Enterprise", "billing_status": "Paid"},
            {"name": "Bob Smith", "email": "bob@yahoo.com", "phone": "+1-555-0143", "subscription_plan": "Growth", "billing_status": "Overdue"},
            {"name": "Charlie Brown", "email": "charlie@outlook.com", "phone": "+1-555-0182", "subscription_plan": "Free", "billing_status": "Unpaid"},
            {"name": "Diana Prince", "email": "diana@amazon.com", "phone": "+1-555-0105", "subscription_plan": "Enterprise", "billing_status": "Paid"},
            {"name": "Evan Wright", "email": "evan@techcorp.com", "phone": "+1-555-0177", "subscription_plan": "Growth", "billing_status": "Paid"}
        ]
        
        customers = []
        for c in customer_data:
            cust = Customer(**c)
            session.add(cust)
            customers.append(cust)
        session.commit()
        
        # 3. Create Orders
        products = ["Cloud hosting block A", "Premium Support Add-on", "SaaS Monthly Subscription", "Enterprise API Access Gateway"]
        orders = []
        for cust in customers:
            # Add 1-2 orders
            num_orders = random.randint(1, 2)
            for _ in range(num_orders):
                ord_item = Order(
                    customer_id=cust.id,
                    product_name=random.choice(products),
                    status=random.choice(["Shipped", "Pending", "Delivered"]),
                    price=round(random.uniform(29.99, 999.99), 2),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                )
                session.add(ord_item)
                orders.append(ord_item)
        session.commit()
        
        # 4. Create Tickets
        tickets = []
        ticket_samples = [
            {"subject": "Billing issue: Charged twice", "description": "I noticed two transactions on my credit card statement for the same monthly sub. Please refund one.", "status": "Open", "priority": "High"},
            {"subject": "API Access connection timeout", "description": "Getting 504 Gateway Timeout when trying to fetch logs via the REST API endpoints.", "status": "Escalated", "priority": "High"},
            {"subject": "Downgrade subscription request", "description": "Can you please switch my account from Growth plan to Free starting next billing cycle?", "status": "Closed", "priority": "Low"},
            {"subject": "Delay in delivery of hosting block", "description": "My dashboard still shows pending setup for the premium cloud hosting block ordered yesterday.", "status": "Open", "priority": "Medium"},
            {"subject": "Help with general dashboard navigation", "description": "Where do I configure custom webhook integrations in my dashboard?", "status": "Closed", "priority": "Low"}
        ]
        
        for i, sample in enumerate(ticket_samples):
            cust = customers[i % len(customers)]
            t = Ticket(
                customer_id=cust.id,
                subject=sample["subject"],
                description=sample["description"],
                status=sample["status"],
                priority=sample["priority"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
            )
            session.add(t)
            tickets.append(t)
        session.commit()
        
        # 5. Create Analytics Metrics for resolved/closed tickets
        categories = ["Billing", "Technical", "Refund", "General Query"]
        sentiments = ["Positive", "Neutral", "Negative"]
        
        # Seed metrics for closed or open tickets
        for t in tickets:
            metric = AnalyticsMetric(
                ticket_id=t.id,
                handling_time=round(random.uniform(5.5, 45.0), 1),
                csat_score=random.randint(3, 5) if t.status == "Closed" else None,
                sentiment=random.choice(sentiments),
                category=random.choice(categories),
                timestamp=t.created_at + timedelta(hours=random.randint(1, 24))
            )
            session.add(metric)
            
        # Add a few historical analytical metrics (15-20 rows for rich charts)
        for i in range(25):
            t_id = random.choice([t.id for t in tickets])
            metric = AnalyticsMetric(
                ticket_id=t_id,
                handling_time=round(random.uniform(2.0, 60.0), 1),
                csat_score=random.randint(1, 5),
                sentiment=random.choice(sentiments),
                category=random.choice(categories),
                timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            session.add(metric)
            
        # 6. Seed initial Customer Memories
        memories = [
            (customers[0].id, "Prefers communication via Gmail. Visited Noida office last year. Crucial Enterprise client."),
            (customers[0].id, "Complained about double charging in past. Sensitive to billing issues."),
            (customers[1].id, "Needs reminders before monthly invoices are generated. Preferred billing date is 5th of each month."),
            (customers[2].id, "Expressed interest in upgrading if prices decrease by 10%."),
            (customers[3].id, "Tech Lead of client. Strongly prefers API documentation link over step-by-step text.")
        ]
        
        for cust_id, text in memories:
            mem_item = CustomerMemory(customer_id=cust_id, content=text)
            session.add(mem_item)
            
        # 7. Audit log seeding
        audit = AuditLog(
            user_id=admin_user.id,
            action="INITIALIZE_DB",
            details="System database initialized and seeded with mock datasets successfully."
        )
        session.add(audit)
        
        session.commit()
        print("Mock database seeding complete!")
