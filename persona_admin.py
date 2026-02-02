#!/usr/bin/env python3
""" Persona Admin Utility for Venice AI Agents
This script provides a command-line interface for managing agent knowledge bases.
It allows viewing, removing specific facts, and flushing all memories for different personas.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_tools.knowledge_base import KnowledgeBase
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the project root directory")
    sys.exit(1)

def list_available_personas():
    """List all available personas in the data directory."""
    personas_dir = Path("data/personas")
    if not personas_dir.exists():
        return []
    
    personas = []
    for item in personas_dir.iterdir():
        if item.is_dir():
            personas.append(item.name)
    return personas

def main():
    print("=== Venice AI Persona Admin Utility ===")
    print("Manage agent knowledge bases and memories")
    
    # List available personas
    available_personas = list_available_personas()
    print(f"\nAvailable personas: {available_personas if available_personas else 'None found'}")
    
    while True:
        try:
            # Get persona selection
            persona = input("\nEnter persona name (or 'exit' to quit): ").strip()
            if persona.lower() == "exit":
                print("Goodbye!")
                break
                
            if not persona:
                print("Please enter a valid persona name")
                continue
            
            # Initialize knowledge base for selected persona
            kb = KnowledgeBase(persona)
            print(f"✓ Knowledge base initialized (persona: {persona})")
            
            # Show current memory status
            current_facts = kb.get_all_facts()
            print(f"✓ Current memory: {len(current_facts)} facts stored")
            
            if current_facts:
                print("\nCurrent memories (showing last 10):")
                for i, fact in enumerate(current_facts[-10:], 1):
                    print(f" {i}. {fact}")
                if len(current_facts) > 10:
                    print(f" ... and {len(current_facts) - 10} more")
            
            # Memory operations menu
            print(f"\nMemory Management for '{persona}':")
            print("1. Show all facts")
            print("2. Remove a specific memory")
            print("3. Flush all memories")
            print("4. Switch to different persona")
            print("5. Add a memory to a persona's staging area")
            print("6. Exit")
            
            while True:
                choice = input(f"\nEnter your choice (1-6) for '{persona}': ").strip()
                
                if choice == "1":
                    all_facts = kb.get_all_facts()
                    if all_facts:
                        print(f"\nAll facts for '{persona}' ({len(all_facts)} total):")
                        for i, fact in enumerate(all_facts, 1):
                            print(f" {i}. {fact}")
                    else:
                        print(f"No facts stored for '{persona}'")
                elif choice == "2":
                    statement = input("Enter the exact statement to remove: ").strip()
                    if statement:
                        kb.flush_fact(statement)
                    else:
                        print("No statement provided")
                elif choice == "3":
                    confirm = input(f"Are you sure you want to delete ALL memories for '{persona}'? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        kb.flush_all()
                        print("✓ All memories have been flushed")
                    else:
                        print("Operation cancelled")
                elif choice == "4":
                    print(f"Switching from '{persona}'...")
                    break
                elif choice == "5":
                    target_persona = input("Enter target persona name: ").strip()
                    if not target_persona:
                        print("Please enter a valid target persona name")
                        continue
                    
                    statement = input("Enter the statement to store in staging: ").strip()
                    if not statement:
                        print("Please enter a statement to store")
                        continue
                    
                    try:
                        target_kb = KnowledgeBase(target_persona)
                        target_kb.store_fact_staging(statement)
                        print(f"✓ Statement stored in staging area for '{target_persona}'")
                        
                        # Show updated staging status
                        staging_facts = target_kb.get_staging_facts()
                        print(f"Staging area now has {len(staging_facts)} fact(s)")
                    except Exception as e:
                        print(f"Error storing statement: {e}")
                elif choice == "6":
                    print("Goodbye!")
                    return
                else:
                    print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6")
                    
                # Update memory status after operations
                updated_facts = kb.get_all_facts()
                print(f"\nMemory status: {len(updated_facts)} facts stored")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"Error during operation: {e}")

if __name__ == "__main__":
    main()