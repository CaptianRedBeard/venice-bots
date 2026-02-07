# Venice Bots

An architectural showcase detailing the evolution of AI agents from a simple stateless responder to a sophisticated, secure, and intelligent multi-agent system. This project documents the step-by-step construction of a powerful cognitive framework. Each agent version represents a major conceptual leap, building on the stable foundation of its predecessor.

## Motivation

This project explores the practical mechanics of how multiple AI agents can work together within a modular, scalable architecture. The primary goals are:

- **Understanding**: To deeply understand how agents, tools, memory systems, and orchestration layers interact in a production-like environment.
- **Iterative Development**: To demonstrate how complex systems evolve through incremental improvements, with each version building upon the stable foundation of its predecessor.
- **Practical Implementation**: To create reusable components that separate concerns between conversation, memory, tool use, and planning, enabling rapid prototyping of specialized agents.

The architecture is built on **separation of concerns**. We've separated an agent's "personality" from its "thinking" and its "tools":

- **Persona System:** Defines an agent's identity, memory, security permissions (ACLs), and behavior via simple `config.json` files.
- **Cognitive Engine (`core_tools/`):** A pluggable set of tools for memory, orchestration, and creative tasks. Agents are thin shells that wire these components together.

## Quick Start

### Prerequisites

- Python 3.8+
- A Venice.ai API key

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

3.  **Configure API Key & Models**
    - Create a `.env` file in the project root.
    - Add your Venice.ai API key: `VENICE_API_KEY=your_api_key_here`
    - (Optional) Review default model roles in `config/models.json`.

### Running an Agent

The `agent_v11` showcase is the recommended starting point for our modern, stable architecture.

```bash
# Run the new stable personal journaling agent
python -m agents.agent_v11_the_captains_log.agent_v11

# Run the stateless agent that pioneered the tool-first architecture
python -m agents.agent_v10_the_tool_first_agent.agent_v10

# Run the foundational stateful agent
python -m agents.agent_v07_the_secure_learner.agent_v07
```

### Managing Models

This project uses a centralized model management system. You can discover available models and update their assignments using the provided admin script.

```bash
# Discover all available models from the Venice API
python manage_models.py --discover

# View the current model-to-role assignments
python manage_models.py --status

# Interactively update a model assignment
python manage_models.py --update
```

### Managing Memories

Use the CLI tool to view, add, or delete memories for any persona.

```bash
python persona_admin.py
```

## Usage

### The Agent Evolution

#### The Modern Architecture (`v07` - `v11`)

The culmination of the project, featuring a production-ready, multi-agent system with a robust, scalable architecture.

##### `agent_v11_the_captains_log` (Stable Proof-of-Concept)
A powerful personal journaling agent that serves as the stable baseline for the project's new architecture. It demonstrates a robust tool system and a simple, reliable orchestration flow.
- **Reliability:** Features a simplified orchestration logic that prioritizes stability.
- **Intelligence:** Uses an LLM to dynamically discover headers in the journal template and select the correct section for notes.
- **Extensibility:** Built on a new, self-describing tool registry that makes the system easy to extend.

##### `agent_v10_the_tool_first_agent` (Stateless Standard)
The new standard for building reliable, stateless agents. It implements a "Classify -> Execute -> Synthesize" workflow that removes the LLM from the critical path of tool selection, dramatically improving reliability for task-oriented interactions.

##### `agent_v09_the_code_analyst` (Stateless Specialist)
A stateless agent designed to analyze codebases. It served as the proof-of-concept for the "Tool-First" architecture, demonstrating its effectiveness in a real-world domain.

##### `agent_v08_the_keeper_of_eldoria` (Creative Showcase)
A world-building and lore management assistant for a TTRPG campaign, demonstrating the framework's versatility:
- **Intelligence:** Recalls world lore and the user's preferences for contextually relevant brainstorming.
- **Specialization:** Uses a custom `BrainstormTool` for creative generation.
- **Security:** Reads user data but only writes to its own world lore, respecting the ACL system.

##### `agent_v07_the_secure_learner` (Stateful Foundation)
The most significant architectural leap for stateful agents. This is the stable, intelligent platform for the entire modern system:
- **Identity-Based:** Entire persona is defined by a `config.json` file.
- **Secure:** Enforces memory access via a strict persona-based ACL system.
- **Intelligent Memory:** Features a `MemoryManager` that resolves knowledge conflicts and deduplicates facts.

#### The Historical Evolution (`v01` - `v06`)

These early versions document the iterative process of building the core components.

##### `agent_v06_the_learner`
Introduced persistent memory, allowing an agent to learn and recall facts across conversations.

##### `agent_v05_simple_orchestrator`
Introduced the "separation of concerns" pattern, delegating planning and execution to the `SimpleOrchestrator` tool.

##### `agent_v04_tool_user`
The first agent to use external tools, demonstrating how an agent can extend its capabilities.

##### `agent_v03_conversationalist`
A step up in conversational ability, maintaining a basic turn-by-turn dialogue.

##### `agent_v01_simple_responder`
The humble beginning. A single-file, stateless agent that responds to a prompt.

### Core Tools

| Tool | Purpose |
| :--- | :--- |
| **`model_manager.py`** | The central abstraction for model selection, providing a role-based API to agents. |
| **`model_discovery_tool.py`** | Fetches live model metadata from the Venice API, with caching for performance. |
| **`llm_function_caller.py`** | A stateless "brain" that uses an LLM to parse natural language into structured tool calls. |
| **`tool_registry.py`** | A dynamic registry for self-describing tools, making the system modular and extensible. |
| **`journal_manager_tool.py`** | A robust tool for handling all file I/O, templating, and date parsing for journaling agents. |
| **`summarizer_tool.py`** | A reusable tool for summarizing long blocks of text into concise bullet points. |
| **`orchestrator.py`** | The original cognitive engine for stateful agents. Manages the "Recall -> Plan -> Execute -> Memorize" workflow. |
| **`memory_manager.py`** | The intelligent memory layer. Uses an LLM to resolve knowledge conflicts. |
| **`knowledge_base.py`** | The secure, persistent storage layer with ACL enforcement. |
| **`file_system_tool.py`** | The primary interface for agents to securely interact with the local file system. |
| **`brainstorm_tool.py`** | A generative tool for creative tasks, used by `agent_v08`. |

## Contributing

We are open to suggestions, feedback, and collaboration as we work out the basic tools and architecture. Since the project is in active development, the core APIs and structures are subject to change. Feel free to open issues or discussions with ideas, but please note that major feature integration may be deferred until the foundational components are solidified.

## License

This project is open-sourced under the MIT License.