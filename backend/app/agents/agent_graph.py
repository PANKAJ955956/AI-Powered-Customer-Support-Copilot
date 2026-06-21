import os
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from backend.app.config import settings
from backend.app.rag.pipeline import retrieve_context
from backend.app.memory.memory_manager import memory_manager
from backend.app.tools.crm_tools import crm_tools_list

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    customer_id: int
    query: str
    chat_history: List[Dict[str, Any]]
    memories: List[str]
    context: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_outputs: List[Dict[str, Any]]
    response: str
    confidence_score: float
    escalate: bool
    category: str
    memories_updated: List[str]

# Initialize LLM safely
llm_available = bool(settings.OPENAI_API_KEY)
if llm_available:
    try:
        # GPT-4o for production-grade agent reasoning
        llm = ChatOpenAI(
            model="gpt-4o",
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.2
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChatOpenAI: {e}")
        llm_available = False
else:
    logger.warning("OPENAI_API_KEY is missing. Utilizing mock agent logic.")

def gather_context_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Retrieves RAG documents and Mem0/local memory profile."""
    customer_id = state["customer_id"]
    query = state["query"]
    
    logger.info(f"Gathering context for query: {query}")
    
    # 1. Retrieve memories
    memories = memory_manager.get_memories(customer_id)
    
    # 2. Retrieve RAG FAQs/policies
    context = retrieve_context(query, limit=3)
    
    return {
        "memories": memories,
        "context": context,
        "tool_calls": [],
        "tool_outputs": []
    }

def determine_action_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Decides if we need to call tools or if we have enough info."""
    query = state["query"].lower()
    customer_id = state["customer_id"]
    
    tool_calls = []
    
    # Heuristic determination or LLM-based tool call selector.
    # In a full LangChain setup, we bind tools to LLM. For robust, deterministic
    # behavior, we execute relevant CRM tools based on keywords or intent.
    # This prevents hallucination and guarantees tool data is fetched correctly.
    if "profile" in query or "user info" in query or "who is" in query or "customer info" in query:
        tool_calls.append({"name": "get_customer_profile", "args": {"customer_id": customer_id}})
    if "billing" in query or "payment" in query or "charged" in query or "invoice" in query:
        tool_calls.append({"name": "get_billing_status", "args": {"customer_id": customer_id}})
    if "ticket" in query or "complain" in query or "history" in query or "previous support" in query:
        tool_calls.append({"name": "get_previous_tickets", "args": {"customer_id": customer_id}})
    if "plan" in query or "subscription" in query or "tier" in query or "downgrade" in query or "upgrade" in query:
        tool_calls.append({"name": "get_subscription_plan", "args": {"customer_id": customer_id}})
    if "order" in query or "package" in query or "purchased" in query or "shipping" in query or "pending" in query:
        tool_calls.append({"name": "check_order_status", "args": {"customer_id": customer_id}})
        
    return {"tool_calls": tool_calls}

def execute_tools_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Executes tool actions dynamically."""
    tool_calls = state.get("tool_calls", [])
    tool_outputs = []
    
    # Dictionary of tools
    tools_map = {t.name: t for t in crm_tools_list}
    
    for tc in tool_calls:
        tool_name = tc["name"]
        args = tc["args"]
        if tool_name in tools_map:
            logger.info(f"Executing tool {tool_name} with args {args}")
            try:
                # Call langchain tool
                output = tools_map[tool_name].invoke(args)
                tool_outputs.append({
                    "tool": tool_name,
                    "input": args,
                    "output": output
                })
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_outputs.append({
                    "tool": tool_name,
                    "input": args,
                    "error": str(e)
                })
                
    return {"tool_outputs": tool_outputs}

def generate_response_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Synthesizes final reply, category, confidence, and checks if escalation is required."""
    query = state["query"]
    customer_id = state["customer_id"]
    memories = state.get("memories", [])
    context = state.get("context", [])
    tool_outputs = state.get("tool_outputs", [])
    
    # 1. Format context for prompt
    context_str = "\n".join([f"- {c['document']} (Source: {c['metadata'].get('source', 'unknown')})" for c in context])
    memories_str = "\n".join([f"- {m}" for m in memories])
    
    tools_str = ""
    for o in tool_outputs:
        if "error" in o:
            tools_str += f"\nTool '{o['tool']}' failed: {o['error']}"
        else:
            tools_str += f"\nTool '{o['tool']}' returned:\n{o['output']}"
            
    # 2. Call OpenAI or use local Mock Response
    if llm_available:
        try:
            system_msg = (
                "You are an enterprise AI Customer Support Copilot assisting a human support agent.\n"
                "Your goal is to formulate a professional, personalized suggested response for the customer, "
                "a confidence score, a ticket category, and determine whether this ticket needs human escalation.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. Base your answer strictly on the facts from the Knowledge Base and CRM Tool outputs.\n"
                "2. If the user query is angry or cannot be answered using the provided tools/kb, suggest escalation (escalate = true).\n"
                "3. Provide a JSON response format. You MUST return ONLY a JSON block containing:\n"
                "   - 'suggested_reply': The response markdown text to send to the customer.\n"
                "   - 'confidence_score': A float between 0.0 and 1.0 based on how well the context covers the query.\n"
                "   - 'escalate': Boolean indicating if the ticket needs support agent manual review or escalation.\n"
                "   - 'category': The ticket category ('Billing', 'Technical', 'Refund', or 'General Query').\n\n"
                f"--- CUSTOMER MEMORY PROFILE ---\n{memories_str or 'No history'}\n\n"
                f"--- RETRIEVED KNOWLEDGE BASE articles ---\n{context_str or 'No relevant policy documents found.'}\n\n"
                f"--- RETRIEVED CRM DATA via TOOLS ---\n{tools_str or 'No CRM tool data fetched.'}\n"
            )
            
            human_msg = f"Customer Support Query:\n'{query}'"
            
            response = llm.invoke([
                SystemMessage(content=system_msg),
                HumanMessage(content=human_msg)
            ])
            
            # Clean LLM response markdown formatting
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            
            # Extract and update memories in background
            memory_input = f"Customer Query: {query}\nSuggested Reply: {data.get('suggested_reply')}"
            memory_manager.add_memory(customer_id, memory_input)
            new_memories = memory_manager.get_memories(customer_id)
            
            return {
                "response": data.get("suggested_reply", ""),
                "confidence_score": data.get("confidence_score", 0.8),
                "escalate": data.get("escalate", False),
                "category": data.get("category", "General Query"),
                "memories_updated": new_memories
            }
        except Exception as e:
            logger.error(f"Error during LLM generate: {e}")
            # Fall through to mock logic on exception
            
    # Mock / Fallback logic if LLM is unavailable or crashes
    suggested_reply = "Hello! "
    category = "General Query"
    escalate = False
    confidence = 0.7
    
    query_lower = query.lower()
    if "billing" in query_lower or "charged" in query_lower:
        category = "Billing"
        suggested_reply += "I see that you have a question regarding billing. According to our Refund Policy, you can request a refund within 30 days of purchase. Let me check your account billing status and process this refund if eligible."
        confidence = 0.85
    elif "api" in query_lower or "timeout" in query_lower:
        category = "Technical"
        suggested_reply += "I understand you are facing connection timeouts. Our premium cloud hosting setup takes 10-15 minutes, but if it has exceeded 1 hour, please let me escalate this immediately to our technical operations team."
        escalate = True
        confidence = 0.9
    elif "refund" in query_lower:
        category = "Refund"
        suggested_reply += "To submit a refund, I can verify if your transaction falls within the 30-day window. Please wait while I process the request with our accounts department."
        confidence = 0.8
    else:
        suggested_reply += "Thank you for contacting customer support. I am retrieving your previous ticket logs and account profile to help resolve your request as quickly as possible. How else can I assist you today?"
        
    if "escalate" in query_lower or "manager" in query_lower or "angry" in query_lower:
        escalate = True
        suggested_reply += "\n\n*(Escalating this ticket to a human manager based on priority request)*"
        
    return {
        "response": suggested_reply,
        "confidence_score": confidence,
        "escalate": escalate,
        "category": category,
        "memories_updated": memories
    }

# Build LangGraph workflow
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("gather_context", gather_context_node)
workflow.add_node("determine_action", determine_action_node)
workflow.add_node("execute_tools", execute_tools_node)
workflow.add_node("generate_response", generate_response_node)

# Set Entrypoint
workflow.set_entry_point("gather_context")

# Add edges
workflow.add_edge("gather_context", "determine_action")

# Route conditionally from determine_action:
# If there are tools to call, go to execute_tools, otherwise go to generate_response
def should_call_tools(state: AgentState) -> str:
    if state.get("tool_calls"):
        return "execute_tools"
    return "generate_response"

workflow.add_conditional_edges(
    "determine_action",
    should_call_tools,
    {
        "execute_tools": "execute_tools",
        "generate_response": "generate_response"
    }
)

workflow.add_edge("execute_tools", "generate_response")
workflow.add_edge("generate_response", END)

# Compile graph
agent_graph = workflow.compile()
