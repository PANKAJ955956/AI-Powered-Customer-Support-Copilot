# Architectural Design Document

This document outlines the system architecture, ER schemas, and Agent workflows of the AI-Powered Customer Support Copilot CRM.

## 1. System Components
- **Dashboard UI (Next.js & Fallback HTML SPA)**: Renders the interface for the support agent, featuring active search dropdowns, order timelines, audit trails, and conversational inputs.
- **FastAPI Application Gateway**: Authenticates requests, exposes analytics dashboards, handles document uploads, and executes agent graph queries.
- **LangGraph Conversational Agent**: Resolves support intent, retrieves relevant context from databases, executes external API mocks via LangChain tools, and compiles replies.
- **ChromaDB Vector Store**: Indexes chunks of company policies (extracted using PyPDF) to run semantic similarity queries on customer inputs.
- **PostgreSQL Relational Storage**: Stores transaction records, ticket queues, admin credentials, audit logs, and memories.

---

## 2. Dynamic Workflow Execution
```mermaid
sequenceDiagram
    autonumber
    Agent UI->>FastAPI: Query Copilot (Customer ID, Query)
    FastAPI->>LangGraph: Run Agent State
    Note over LangGraph: Node: gather_context
    LangGraph->>Mem0 Memory: Load Customer Memories
    LangGraph->>ChromaDB: Query Semantic FAQ Match
    Note over LangGraph: Node: determine_action
    alt Intent requires CRM data
        LangGraph->>CRM Tools: execute get_customer_profile / check_order_status
        CRM Tools-->>LangGraph: returns JSON payload
    end
    Note over LangGraph: Node: generate_response
    LangGraph->>OpenAI GPT-4o: Run prompt (Context + Tools + Query)
    OpenAI GPT-4o-->>LangGraph: returns Suggested Reply & Metrics
    LangGraph->>Mem0 Memory: Extract & update memory changes
    LangGraph->>FastAPI: Return state output
    FastAPI->>SQL DB: Write Audit log & Analytics metric
    FastAPI-->>Agent UI: Return final response JSON
```

---

## 3. Database Entity-Relationship Model
```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string hashed_password
        string role
        datetime created_at
    }
    CUSTOMERS {
        int id PK
        string name
        string email UK
        string phone
        string subscription_plan
        string billing_status
        datetime created_at
    }
    TICKETS {
        int id PK
        int customer_id FK
        string subject
        string description
        string status
        string priority
        datetime created_at
        datetime updated_at
    }
    ORDERS {
        int id PK
        int customer_id FK
        string product_name
        string status
        float price
        datetime created_at
    }
    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string details
        datetime timestamp
    }
    ANALYTICS {
        int id PK
        int ticket_id FK
        float handling_time
        int csat_score
        string sentiment
        string category
        datetime timestamp
    }

    CUSTOMERS ||--o{ TICKETS : has
    CUSTOMERS ||--o{ ORDERS : places
    USERS ||--o{ AUDIT_LOGS : performs
    TICKETS ||--o| ANALYTICS : analyzes
```
