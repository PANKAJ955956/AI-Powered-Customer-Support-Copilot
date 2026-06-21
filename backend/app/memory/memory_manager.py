import logging
from sqlmodel import Session, select
from backend.app.config import settings
from backend.app.database.connection import engine
from backend.app.database.models import CustomerMemory
import openai

logger = logging.getLogger(__name__)

# Try to initialize mem0. Fall back to local DB memories if import fails.
MEM0_AVAILABLE = False
try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except Exception as e:
    logger.warning(f"Mem0 library not available or failed to import: {e}. Using local database fallback for memory storage.")

class MemoryManager:
    def __init__(self):
        self.use_mem0 = False
        self.mem0_client = None
        
        # Only use Mem0 if the package is imported and the API key is present
        if MEM0_AVAILABLE and settings.MEM0_API_KEY:
            try:
                # Mem0 configuration
                config = {
                    "vector_store": {
                        "provider": "chroma",
                        "config": {
                            "collection_name": "mem0_collection",
                            "path": "./chroma_mem0_db"
                        }
                    }
                }
                self.mem0_client = Memory.from_config(config)
                self.use_mem0 = True
                logger.info("Mem0 Memory client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0 Client: {e}. Falling back to SQLite memory storage.")
                self.use_mem0 = False

    def add_memory(self, customer_id: int, interaction: str, db_session: Session = None):
        """Adds a memory snippet extracted from a customer support interaction."""
        logger.info(f"Adding memory for customer ID {customer_id}")
        
        if self.use_mem0:
            try:
                # Standard Mem0 add memory
                self.mem0_client.add(interaction, user_id=f"cust_{customer_id}")
                return
            except Exception as e:
                logger.error(f"Mem0 add memory failed: {e}. Falling back to SQL.")

        # Fallback implementation: use OpenAI (or simple extraction) to get key bullet points
        # and store them in the SQL database.
        extracted_facts = []
        if settings.OPENAI_API_KEY:
            try:
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = (
                    "You are an AI Memory Extractor. Extract concise, key details, customer preferences, "
                    "past complaints, purchase habits, or technical configurations mentioned in this support interaction. "
                    "Only extract facts that are useful to remember for future conversations. "
                    "Return ONLY the facts as a bullet-pointed list, one per line (starting with '- '). "
                    "Do not repeat existing common knowledge. If nothing important is mentioned, return 'None'.\n\n"
                    f"Interaction:\n{interaction}"
                )
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                text = response.choices[0].message.content or ""
                for line in text.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") and len(line) > 3:
                        fact = line[2:]
                        if "none" not in fact.lower():
                            extracted_facts.append(fact)
            except Exception as e:
                logger.error(f"Failed to extract memories via OpenAI: {e}")
                
        # If OpenAI fails or returns empty, save the raw interaction snippet (truncated)
        if not extracted_facts:
            # Simple heuristic backup
            words = interaction.split()
            snippet = " ".join(words[:20]) + "..."
            extracted_facts.append(f"Recent support interaction: '{snippet}'")

        # Save facts in the local database
        session_to_use = db_session
        close_session = False
        if not session_to_use:
            session_to_use = Session(engine)
            close_session = True
            
        try:
            for fact in extracted_facts:
                mem = CustomerMemory(customer_id=customer_id, content=fact)
                session_to_use.add(mem)
            session_to_use.commit()
            logger.info(f"Successfully saved {len(extracted_facts)} local memories for customer {customer_id}")
        except Exception as e:
            logger.error(f"Failed to save local database memory: {e}")
        finally:
            if close_session:
                session_to_use.close()

    def get_memories(self, customer_id: int, db_session: Session = None) -> list[str]:
        """Gets all memories associated with a customer."""
        if self.use_mem0:
            try:
                mem_data = self.mem0_client.get_all(user_id=f"cust_{customer_id}")
                if mem_data and isinstance(mem_data, list):
                    return [item.get("memory", "") for item in mem_data if "memory" in item]
            except Exception as e:
                logger.error(f"Mem0 get memories failed: {e}. Falling back to SQL.")

        # Fallback: Fetch from SQL database
        session_to_use = db_session
        close_session = False
        if not session_to_use:
            session_to_use = Session(engine)
            close_session = True
            
        try:
            statement = select(CustomerMemory).where(CustomerMemory.customer_id == customer_id)
            results = session_to_use.exec(statement).all()
            return [mem.content for mem in results]
        except Exception as e:
            logger.error(f"Failed to query local database memory: {e}")
            return []
        finally:
            if close_session:
                session_to_use.close()

    def delete_memories(self, customer_id: int, db_session: Session = None):
        """Clears all memories for a customer."""
        if self.use_mem0:
            try:
                self.mem0_client.delete_all(user_id=f"cust_{customer_id}")
            except Exception as e:
                logger.error(f"Mem0 delete memories failed: {e}")

        # Fallback: delete from local DB
        session_to_use = db_session
        close_session = False
        if not session_to_use:
            session_to_use = Session(engine)
            close_session = True
            
        try:
            statement = select(CustomerMemory).where(CustomerMemory.customer_id == customer_id)
            results = session_to_use.exec(statement).all()
            for r in results:
                session_to_use.delete(r)
            session_to_use.commit()
            logger.info(f"Cleared local memories for customer {customer_id}")
        except Exception as e:
            logger.error(f"Failed to delete local memories: {e}")
        finally:
            if close_session:
                session_to_use.close()

# Global memory instance
memory_manager = MemoryManager()
