# Technical Interview Questions & Answers

A collection of interview questions and answers concerning the AI-Powered Customer Support Copilot CRM system.

---

## 1. Why did you select LangGraph instead of LangChain's standard AgentExecutor?
**Answer**:
- **Cyclic Graph Support**: Support tickets frequently require multiple recursive correction loops (e.g. Query RAG -> Call Billing Tool -> Realize account is overdue -> Query billing policies -> Reformulate Response). LangGraph makes this cyclic routing deterministic using explicit state nodes and conditional edges.
- **State Persistence**: LangGraph maintains state dictionaries directly, giving developers full visibility and auditing capabilities over the internal state between node jumps.
- **Predictable Control**: Standard AgentExecutor relies heavily on LLM reasoning to decide when to finish. With LangGraph, we can force specific pipelines (like gathering context before starting tools) via hardcoded edges, reducing token usage and latency.

---

## 2. How did you implement Mem0 memory persistence, and how does your custom local fallback operate?
**Answer**:
- **Mem0 Core**: Mem0 uses vector similarity matching to merge new conversation statements with existing memories (e.g., if a user previously said "I use Gmail" and now says "Send alerts to Gmail", it merges them).
- **SQLite Database Fallback**: If Mem0 credentials are not available, the application calls a custom backup memory extractor:
  1. We send the conversation text to `gpt-4o-mini` with a specialized prompt requesting it to extract atomic facts (e.g., "Prefers invoices on the 5th", "Encountered a hosting delay").
  2. We parse the list of facts and insert them into the `customer_memories` SQL relational table.
  3. During subsequent runs, these memories are loaded and appended to the agent's context.

---

## 3. How do you prevent hallucination in the RAG retrieval engine?
**Answer**:
- **Strict Context Prompting**: The system prompt forces the LLM to write replies based *only* on context documents retrieved from ChromaDB or JSON structures returned by the CRM tools.
- **Confidence Scoring**: The agent outputs a confidence score based on how well the context covers the query. If the context is missing (score is low), the agent triggers the `escalate = true` flag.
- **Dynamic Escalation Routing**: Any query that doesn't find matches in the vector database is flagged for human support review rather than allowing the agent to guess.

---

## 4. How did you resolve library installation and startup failures for Windows developers?
**Answer**:
- **Resilient Fallbacks**: Python libraries like `chromadb` and `mem0` can fail to build on Windows systems that lack native C++ compilers. To bypass this, we implemented dynamic try-except blocks:
  - If `chromadb` fails, the system switches to `SimpleVectorStore`, a lightweight Python class using substring search and basic Jaccard word-overlap matching.
  - If `mem0` fails, the system uses SQLite to store and fetch customer memories.
- This ensures the FastAPI server is highly portable and starts immediately, allowing testing on any environment.

---

## 5. What strategies did you apply to optimize latency?
**Answer**:
- **Lightweight Fallbacks**: We default to `gpt-4o-mini` for memory extraction in the background, conserving `gpt-4o` for the final copilot response generation where advanced logic is required.
- **Targeted Tool Calls**: Instead of binding all CRM tools directly to the model (which increases latency by forcing the LLM to inspect all signatures and write parameters), we analyze keywords to execute matching tools beforehand. This reduces the number of LLM round-trips.
