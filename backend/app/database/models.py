from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="Agent") # "Agent" or "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    phone: str
    subscription_plan: str # "Free", "Growth", "Enterprise"
    billing_status: str # "Paid", "Overdue", "Unpaid"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tickets: List["Ticket"] = Relationship(back_populates="customer")
    orders: List["Order"] = Relationship(back_populates="customer")
    memories: List["CustomerMemory"] = Relationship(back_populates="customer")

class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    subject: str
    description: str
    status: str = Field(default="Open") # "Open", "Closed", "Escalated"
    priority: str = Field(default="Medium") # "Low", "Medium", "High"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    customer: Customer = Relationship(back_populates="tickets")
    analytics: Optional["AnalyticsMetric"] = Relationship(back_populates="ticket")

class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    product_name: str
    status: str # "Shipped", "Pending", "Delivered", "Cancelled"
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    customer: Customer = Relationship(back_populates="orders")

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsMetric(SQLModel, table=True):
    __tablename__ = "analytics_metrics"
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: Optional[int] = Field(default=None, foreign_key="tickets.id")
    handling_time: float # in minutes
    csat_score: Optional[int] = Field(default=None) # 1-5 rating
    sentiment: str # "Positive", "Neutral", "Negative"
    category: str # "Billing", "Technical", "Refund", "General Query"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    ticket: Optional[Ticket] = Relationship(back_populates="analytics")

class CustomerMemory(SQLModel, table=True):
    __tablename__ = "customer_memories"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    content: str # Memory string e.g., "Prefers email communications. Had a late delivery issue in Dec."
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    customer: Customer = Relationship(back_populates="memories")
