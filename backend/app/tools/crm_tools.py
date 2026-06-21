import json
from langchain.tools import tool
from sqlmodel import Session, select
from backend.app.database.connection import engine
from backend.app.database.models import Customer, Ticket, Order
import logging

logger = logging.getLogger(__name__)

@tool
def get_customer_profile(customer_id: int) -> str:
    """Retrieves customer profile information including name, email, phone, subscription tier, and created date."""
    with Session(engine) as session:
        statement = select(Customer).where(Customer.id == customer_id)
        cust = session.exec(statement).first()
        if not cust:
            return json.dumps({"error": f"Customer with ID {customer_id} not found."})
        
        return json.dumps({
            "id": cust.id,
            "name": cust.name,
            "email": cust.email,
            "phone": cust.phone,
            "subscription_plan": cust.subscription_plan,
            "billing_status": cust.billing_status,
            "created_at": cust.created_at.isoformat()
        }, indent=2)

@tool
def get_previous_tickets(customer_id: int) -> str:
    """Retrieves all previous support tickets for the customer, showing subjects, descriptions, priority levels, and statuses."""
    with Session(engine) as session:
        statement = select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc())
        tickets = session.exec(statement).all()
        if not tickets:
            return json.dumps({"message": f"No support tickets found for customer ID {customer_id}."})
            
        ticket_list = []
        for t in tickets:
            ticket_list.append({
                "ticket_id": t.id,
                "subject": t.subject,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "created_at": t.created_at.isoformat()
            })
        return json.dumps(ticket_list, indent=2)

@tool
def get_billing_status(customer_id: int) -> str:
    """Retrieves customer subscription billing status (e.g. Paid, Overdue, Unpaid)."""
    with Session(engine) as session:
        statement = select(Customer).where(Customer.id == customer_id)
        cust = session.exec(statement).first()
        if not cust:
            return json.dumps({"error": f"Customer with ID {customer_id} not found."})
            
        return json.dumps({
            "customer_id": cust.id,
            "name": cust.name,
            "billing_status": cust.billing_status,
            "subscription_plan": cust.subscription_plan
        }, indent=2)

@tool
def get_subscription_plan(customer_id: int) -> str:
    """Retrieves the customer's active subscription tier (e.g. Free, Growth, Enterprise)."""
    with Session(engine) as session:
        statement = select(Customer).where(Customer.id == customer_id)
        cust = session.exec(statement).first()
        if not cust:
            return json.dumps({"error": f"Customer with ID {customer_id} not found."})
            
        return json.dumps({
            "customer_id": cust.id,
            "name": cust.name,
            "subscription_plan": cust.subscription_plan
        }, indent=2)

@tool
def check_order_status(customer_id: int) -> str:
    """Retrieves the status of all product orders placed by the customer, including delivery state and price details."""
    with Session(engine) as session:
        statement = select(Order).where(Order.customer_id == customer_id).order_by(Order.created_at.desc())
        orders = session.exec(statement).all()
        if not orders:
            return json.dumps({"message": f"No orders found for customer ID {customer_id}."})
            
        order_list = []
        for o in orders:
            order_list.append({
                "order_id": o.id,
                "product_name": o.product_name,
                "status": o.status,
                "price": o.price,
                "created_at": o.created_at.isoformat()
            })
        return json.dumps(order_list, indent=2)

# List of tools to be used by the agent
crm_tools_list = [
    get_customer_profile,
    get_previous_tickets,
    get_billing_status,
    get_subscription_plan,
    check_order_status
]
