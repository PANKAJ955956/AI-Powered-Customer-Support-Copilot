# REST API Reference Manual

The Copilot Backend uses a JSON REST API built with FastAPI. All requests must use the correct paths and authentication headers.

---

## Base Path
- Local Server: `http://localhost:8000/api`
- Swagger Documentation Interface: `http://localhost:8000/docs`
- Redoc Reference: `http://localhost:8000/redoc`

---

## 1. Authentication Endpoints

### User Registration
- **URL**: `/auth/register`
- **Method**: `POST`
- **Content Type**: `application/x-www-form-urlencoded` or `multipart/form-data`
- **Parameters**:
  - `email`: (string) Email Address
  - `password`: (string) Plain text password
  - `role`: (string, default "Agent") User security group (`Agent` or `Admin`)
- **Response (200)**:
  ```json
  {
    "message": "User registered successfully",
    "email": "agent@copilot.com",
    "role": "Agent"
  }
  ```

### User Login (Access Token Exchange)
- **URL**: `/auth/login`
- **Method**: `POST`
- **Content Type**: `application/x-www-form-urlencoded`
- **Parameters**:
  - `username`: (string, maps to email)
  - `password`: (string)
- **Response (200)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "email": "agent@copilot.com",
      "role": "Agent"
    }
  }
  ```

---

## 2. Customer Directory Endpoints

### List Customers
- **URL**: `/customers`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200)**: List of customer objects containing name, subscription plans, and billing states.

### Get Customer Complete Context
- **URL**: `/customers/{customer_id}`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200)**:
  ```json
  {
    "customer": {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice@gmail.com",
      "subscription_plan": "Enterprise"
    },
    "tickets": [ ... ],
    "orders": [ ... ],
    "memories": [ "Prefers email", "Complained of late delivery" ]
  }
  ```

---

## 3. Copilot AI & Memory Services

### Query Copilot Graph
- **URL**: `/copilot/query`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Parameters (Form Data)**:
  - `customer_id`: (integer) ID of the client
  - `query`: (string) Agent prompt or customer text
- **Response (200)**:
  ```json
  {
    "suggested_reply": "Hello Alice, I noticed your premium hosting package...",
    "confidence_score": 0.95,
    "escalate": false,
    "category": "Technical",
    "memories": [ ... ],
    "retrieved_kb": [ ... ]
  }
  ```

### Ingest Knowledge Base PDF (RAG)
- **URL**: `/copilot/upload`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>` (Must be role: Admin)
- **Parameters (Multipart)**:
  - `file`: (Binary PDF file upload)
- **Response (200)**:
  ```json
  {
    "filename": "refund_policy.pdf",
    "chunks_ingested": 12,
    "message": "Knowledge base updated successfully"
  }
  ```

### Clear Customer Memory Profile
- **URL**: `/copilot/memories/{customer_id}`
- **Method**: `DELETE`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200)**:
  ```json
  {
    "message": "Successfully cleared all memories for customer 1."
  }
  ```

---

## 4. Performance & Audit Logs

### Fetch Analytics Metrics
- **URL**: `/analytics/dashboard`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200)**: Returns Average Handling Time, CSAT trends, and Categories counts.

### Fetch Security Audit Trail
- **URL**: `/logs`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <JWT_TOKEN>` (Must be Admin)
- **Response (200)**: List of event logs.
