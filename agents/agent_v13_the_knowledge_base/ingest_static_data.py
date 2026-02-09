#!/usr/bin/env python3
"""
Ingestion script for the Knowledge Base Agent.
Populates the vector and SQL databases with test data.
"""
import sys
from pathlib import Path

# --- FIX: Robustly find the project root ---
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from symphony.context_manager import get_context_manager
from sqlalchemy import create_engine, text

def main():
    print("--- Ingesting Static Data for agent_v13 ---")
    context_manager = get_context_manager()

    # --- 1. Ingest into Vector DB ---
    print("Ingesting documents into Vector DB...")
    # --- FIX: Use the /data directory ---
    kb_path = project_root / "data" / "knowledge_base"
    kb_path.mkdir(parents=True, exist_ok=True) # Use parents=True to create /data if needed

    # Create a wider variety of sample markdown files
    (kb_path / "birthdays.md").write_text("""
    # Company Policy on Birthdays
    The company celebrates every employee's birthday. On their birthday, employees are entitled to a half day off.
    A small cake is provided for the team to celebrate. It's a fun way to show appreciation for our team members.
    """)
    (kb_path / "project_roles.md").write_text("""
    # Project Roles and Responsibilities
    The lead architect is responsible for the overall system design. The AI tooling specialist focuses on integrating and managing AI tools.
    The workflow designer ensures that user workflows are logical and efficient. Each role is critical for project success.
    """)
    (kb_path / "company_history.md").write_text("""
    # A Brief History of Our Company
    Founded in 2020, our company started with a mission to simplify complex workflows using AI.
    We have grown to a team of over 50 people and have helped numerous clients automate their business processes.
    The name 'Symphony' was chosen to represent the harmonious integration of different AI agents working together.
    """)
    (kb_path / "dev_environment.md").write_text("""
    # Development Environment Setup
    All developers are required to use Python 3.10 or newer. The project uses Poetry for dependency management.
    The primary IDE recommended is VS Code with the Python and Docker extensions. All code must pass the flake8 linter.
    """)
    
    # Clear existing docs and ingest new ones
    if context_manager.collection.count() > 0:
        print("Clearing existing vector DB collection...")
        context_manager.chroma_client.delete_collection(name="knowledge_base")
        context_manager.collection = context_manager.chroma_client.get_or_create_collection(name="knowledge_base")

    for file_path in kb_path.glob("*.md"):
        content = file_path.read_text()
        doc_id = file_path.stem
        metadata = {
            "source_file": file_path.name,
            "chunk_id": doc_id,
            "access_level": "public"
        }
        context_manager.add_document_to_vector_db(doc_id, content, metadata)

    # --- 2. Ingest into SQL DB ---
    print("Ingesting user data into SQL DB...")
    engine = context_manager.sql_engine
    with engine.connect() as conn:
        # --- SAFER: Drop the table first to ensure a clean schema ---
        print("Dropping old 'v13_employees' table if it exists...")
        conn.execute(text("DROP TABLE IF EXISTS v13_employees"))

        print("Creating new 'v13_employees' table...")
        conn.execute(text("""
            CREATE TABLE v13_employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                birthday DATE,
                access_level TEXT DEFAULT 'public'
            )
        """))
        
        # Insert sample data
        conn.execute(text("""
            INSERT INTO v13_employees (name, email, birthday, access_level) VALUES
            ('Sarah Chen', 'sarah.chen@example.com', '1990-05-15', 'public'),
            ('Andrew Smith', 'andrew.smith@example.com', '1988-08-22', 'public'),
            ('Ben Carter', 'ben.carter@example.com', '1992-11-30', 'internal'),
            ('Maria Garcia', 'maria.garcia@example.com', '1985-02-10', 'public')
        """))
        conn.commit()

    print("✅ Static data ingestion complete.")
    context_manager.close()

if __name__ == "__main__":
    main()