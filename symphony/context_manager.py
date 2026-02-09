import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class ContextManager:
    """
    The single source of truth for all memory and context retrieval operations.
    Manages connections to a vector database (ChromaDB) and a structured database (SQLite via SQLAlchemy).
    """
    def __init__(self, db_path: str = "data/symphony.db", chroma_path: str = "data/chroma_db"):
        # --- SQL Database Setup (using SQLAlchemy) ---
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.sql_engine = create_engine(f"sqlite:///{self.db_path}")
        self._initialize_sql_db()

        # --- Vector Database Setup ---
        self.chroma_path = Path(chroma_path)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

        # --- Embedding Model ---
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _initialize_sql_db(self):
        """Initializes the SQL database with the required 'users' table."""
        with self.sql_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    birthday DATE,
                    access_level TEXT DEFAULT 'public'
                )
            """))
            conn.commit()

    def add_document_to_vector_db(self, doc_id: str, document: str, metadata: Optional[Dict] = None):
        """Adds a document to the ChromaDB vector store with required metadata."""
        if metadata is None:
            metadata = {}
        # Ensure required metadata fields are present
        if 'access_level' not in metadata:
            metadata['access_level'] = 'public'
        if 'source_file' not in metadata:
            metadata['source_file'] = 'unknown'
        if 'chunk_id' not in metadata:
            metadata['chunk_id'] = doc_id

        embedding = self.embedding_model.encode(document).tolist()
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
        print(f"Added document '{doc_id}' to vector DB.")

    def get_context(self, query: str, agent_acl: dict) -> str:
        """
        Retrieves and synthesizes context from both SQL and Vector databases,
        filtering results based on the agent's ACL and a relevance threshold.
        """
        if not query:
            return "Error: The query cannot be empty."
        
        agent_access_level = agent_acl.get('access_level', 'public')

        # 1. Query Vector DB, filtering by ACL and relevance.
        vector_results = []
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            raw_results = self.collection.query(
                query_embeddings=[query_embedding], 
                n_results=3,
                where={"access_level": agent_access_level},
                include=['documents', 'distances'] # Ensure we get distances
            )
            
            # --- FINAL POLISH: Filter by relevance threshold ---
            RELEVANCE_THRESHOLD = 1 # Cosine distance threshold (0=identical, 1=opposite)
            
            if raw_results['ids'][0]:
                for i in range(len(raw_results['ids'][0])):
                    distance = raw_results['distances'][0][i]
                    if distance < RELEVANCE_THRESHOLD:
                        vector_results.append(raw_results['documents'][0][i])
        except Exception as e:
            print(f"Vector DB query failed: {e}")

        # 2. Query SQL DB, only if the query seems to be about a user
        sql_results = []
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["birthday", "user", "who is", "email"]):
            try:
                with self.sql_engine.connect() as conn:
                    stmt = text("SELECT name, email, birthday FROM v13_employees WHERE access_level = :access_level")
                    db_results = conn.execute(stmt, {"access_level": agent_access_level}).fetchall()
                    sql_results = [f"User: {row.name}, Email: {row.email}, Birthday: {row.birthday}" for row in db_results]
            except Exception as e:
                print(f"SQL query failed: {e}")

        # 3. Synthesize results
        context_parts = []
        if vector_results:
            context_parts.append("--- Knowledge Base ---\n" + "\n\n".join(vector_results))
        if sql_results:
            context_parts.append("--- User Data ---\n" + "\n".join(sql_results))

        if not context_parts:
            return "No relevant information found."

        return "\n\n".join(context_parts)

    def close(self):
        """Closes all database connections."""
        self.sql_engine.dispose()
        print("Database connections closed.")

# --- Singleton instance for easy access across the application ---
_context_manager_instance = None
def get_context_manager() -> ContextManager:
    """Returns a singleton instance of the ContextManager."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance
