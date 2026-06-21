import os
import uuid
import logging
from pypdf import PdfReader
from backend.app.rag.chroma_client import chroma_db

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Simple recursive character-like chunking."""
    if not text:
        return []
        
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start += (chunk_size - chunk_overlap)
    return chunks

def ingest_pdf(file_path: str, source_name: str = None) -> int:
    """Ingests a PDF file, chunks its text, and stores it in ChromaDB."""
    if not os.path.exists(file_path):
        logger.error(f"PDF file not found: {file_path}")
        return 0
        
    try:
        reader = PdfReader(file_path)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                
        if not text.strip():
            logger.warning(f"No text extracted from PDF: {file_path}")
            return 0
            
        chunks = chunk_text(text)
        metadatas = []
        ids = []
        
        file_basename = source_name or os.path.basename(file_path)
        
        for idx, chunk in enumerate(chunks):
            metadatas.append({
                "source": file_basename,
                "chunk_index": idx,
                "ingested_at": str(os.path.getmtime(file_path))
            })
            ids.append(f"{file_basename}_{idx}_{uuid.uuid4().hex[:6]}")
            
        chroma_db.add_documents(chunks, metadatas, ids)
        logger.info(f"Successfully ingested {len(chunks)} chunks from PDF: {file_path}")
        return len(chunks)
    except Exception as e:
        logger.error(f"Failed to ingest PDF {file_path}: {e}")
        return 0

def retrieve_context(query: str, limit: int = 3) -> list[dict]:
    """Retrieve top matched context documents from the vector database."""
    return chroma_db.similarity_search(query, k=limit)

def seed_default_kb():
    """Seed the vector store with basic FAQs and company policies to make it work immediately."""
    faqs = [
        {
            "text": "Refund Policy: Customers can request a full refund within 30 days of purchase for any SaaS monthly subscriptions or hosting packages. Refunds take 5-7 business days to process back to the original payment card. No refunds are allowed after 30 days.",
            "meta": {"source": "refund_policy.txt", "category": "Billing"}
        },
        {
            "text": "SLA Response Times: Enterprise support requests are responded to within 1 hour. Growth plan support tickets are answered within 4 hours. Free tier support is handled on a best-effort basis, usually within 24-48 business hours.",
            "meta": {"source": "support_sla.txt", "category": "Operations"}
        },
        {
            "text": "Premium Cloud Hosting Block: Premium cloud hosting blocks provide automated daily backups, 99.99% uptime SLA, and an integrated content delivery network (CDN). Deployment takes approximately 10-15 minutes from order confirmation. If hosting blocks remain in 'pending setup' state for more than 1 hour, agents should escalate to Devops team.",
            "meta": {"source": "hosting_manual.txt", "category": "Technical"}
        },
        {
            "text": "API Rate Limits: API connections are limited based on tier. Enterprise accounts have a limit of 10,000 requests per minute. Growth plans are limited to 2,000 requests per minute. Free tier accounts can make up to 100 requests per minute. Exceeding limits will return a HTTP 429 Too Many Requests status code.",
            "meta": {"source": "api_limits.txt", "category": "Technical"}
        },
        {
            "text": "Canceling Subscription: To cancel a subscription, users should go to Billing Settings in their dashboard, click 'Cancel Plan', and confirm. The subscription will remain active until the end of the current billing cycle, after which it will downgrade to the Free tier.",
            "meta": {"source": "account_faq.txt", "category": "General"}
        }
    ]
    
    chunks = [f["text"] for f in faqs]
    metadatas = [f["meta"] for f in faqs]
    ids = [f"faq_{i}" for i in range(len(faqs))]
    
    chroma_db.add_documents(chunks, metadatas, ids)
    logger.info("Default Knowledge Base (FAQ) seeded successfully.")
