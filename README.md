# Venice Bots

An architectural showcase detailing the evolution of AI agents from a simple stateless responder to a sophisticated, secure, and intelligent multi-agent system.

This project documents the step-by-step construction of a powerful cognitive framework. Each agent version (`v01` through `v08`) represents a major conceptual leap, building on the stable foundation of its predecessor.

## Core Philosophy

The architecture is built on **separation of concerns**. We've separated an agent's "personality" from its "thinking" and its "tools."

-   **Persona System:** Defines an agent's identity, memory, security permissions (ACLs), and behavior via simple `config.json` files.
-   **Cognitive Engine (`core_tools/`):** A pluggable set of tools for memory, orchestration, and creative tasks. Agents are thin shells that wire these components together.

## The Agent Evolution

### The Modern Architecture (`v07` & `v08`)

The culmination of the project, featuring a production-ready, multi-agent system.

#### `agent_v08_the_keeper_of_eldoria` (Showcase)
A world-building and lore management assistant for a TTRPG campaign, demonstrating the framework's versatility.
-   **Intelligence:** Recalls world lore and the user's preferences for contextually relevant brainstorming.
-   **Specialization:** Uses a custom `BrainstormTool` for creative generation.
-   **Security:** Reads user data but only writes to its own world lore, respecting the ACL system.

#### `agent_v07_the_secure_learner` (The Foundation)
The most significant architectural leap. This is the stable, intelligent platform for the entire modern system.
-   **Identity-Based:** Entire persona is defined by a `config.json` file.
-   **Secure:** Enforces memory access via a strict persona-based ACL system.
-   **Intelligent Memory:** Features a `MemoryManager` that resolves knowledge conflicts and deduplicates facts without impacting conversation speed.

### The Historical Evolution (`v01` - `v06`)

These early versions document the iterative process of building the core components.

#### `agent_v06_the_learner`
Introduced persistent memory, allowing an agent to learn and recall facts across conversations.

#### `agent_v05_simple_orchestrator`
Introduced the "separation of concerns" pattern, delegating planning and execution to the `SimpleOrchestrator` tool.

#### `agent_v04_tool_user`
The first agent to use external tools, demonstrating how an agent can extend its capabilities.

#### `agent_v03_conversationalist`
A step up in conversational ability, maintaining a basic turn-by-turn dialogue.

#### `agent_v01_simple_responder`
The humble beginning. A single-file, stateless agent that responds to a prompt.

## Core Tools

| Tool | Purpose |
| :--- | :--- |
| **`orchestrator.py`** | The cognitive engine. Manages the "Recall -> Plan -> Execute -> Memorize" workflow. |
| **`memory_manager.py`** | The intelligent memory layer. Uses an LLM to resolve knowledge conflicts. |
| **`knowledge_base.py`** | The secure, persistent storage layer with ACL enforcement. |
| **`brainstorm_tool.py`** | A generative tool for creative tasks, used by `agent_v08`. |

## Getting Started

### Prerequisites
-   Python 3.8+
-   A Venice.ai API key.

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/CaptianRedBeard/venice-bots.git
    cd venice-bots
    ```

2.  **Set Up Environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install python-dotenv openai
    ```

3.  **Configure API Key**
    -   Create a `.env` file in the project root.
    -   Add your Venice.ai API key:
        ```
        VENICE_API_KEY=your_api_key_here
        ```

### Running an Agent
The `agent_v08` showcase is the recommended starting point.

```bash
# Run the final showcase agent
python -m agents.agent_v08_the_keeper_of_eldoria.agent_v08

# Run the foundational modern agent
python -m agents.agent_v07_the_secure_learner.agent_v07
```

### Managing Memories

Use the CLI tool to view, add, or delete memories for any persona.
bash

```bash
python persona_admin.py
```

## License

This project is open-sourced under the MIT License.