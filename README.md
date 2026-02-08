# Venice Bots: A Multi-Agent AI Framework

This project is a continuously evolving framework for building, orchestrating, and managing specialized AI agents. It began as a series of prototypes to explore different architectural patterns and has now matured into "Project Symphony," a robust, decoupled system designed for scalability and maintainability.

## Project History and Evolution

This project's development can be understood in distinct phases, each addressing the limitations of the last.


### Phase 1: The Prototype Era (v1 - v11)
The initial versions were focused on proving the core concepts of agentic AI. This era saw the development of individual agents with increasingly complex internal orchestration, from simple tool-users to secure learners. These agents were invaluable for learning but were ultimately tightly coupled and not designed for a multi-agent system. **They are now considered legacy artifacts and are superseded by the v2.0.0 Symphony framework.**

-   **Agent v08:** A showcase agent demonstrating the initial "Tool-First" architecture.
-   **Agent v09:** A specialized code analyst with granular error handling.
-   **Agent v11:** The "Captains Log," a stable journaling agent that served as the final prototype and baseline for the next phase.

### Phase 2: The Architectural Pivot ("Operation Clean Slate")
With the lessons from the prototypes, we undertook a major refactoring to establish a "Tool-First" architecture. This involved creating self-describing tools and a more modular agent design, which solidified v11 as a stable, working baseline.

### Phase 3: The Framework Era (v2.0.0 - Project Symphony)
The prototype era revealed that a collection of individual agents was not enough. We needed a system to compose them. This led to a complete architectural overhaul to build a decoupled, scalable framework. The legacy systems were sunsetted in favor of a new, powerful core.

## Introducing Project Symphony (v2.0.0)

Symphony is the new core of the framework. It is a decoupled architecture built on a central "Conductor" that orchestrates "Doer" agents and "Standardized" tools. This design solves the scalability and maintainability issues of the prototype era and provides a clean foundation for rapid development.

### The Philosophy: Separation of Concerns

-   **Agents are Doers:** An agent's only job is to use the tools it's given to accomplish a task. It is a pure, stateless executor.
-   **The Conductor is the Brain:** The Conductor is the central orchestrator. It reads a workflow, discovers the right agents and tools, and injects them with the necessary context to execute the plan.
-   **Tools are Standardized:** All tools inherit from a `SymphonyTool` base class, ensuring they can be seamlessly integrated and managed by the Conductor.

## Prerequisites

- Python 3.8 or higher
- A Venice AI API key

## Quick Start

### 1. Initialize the Project

First, run the setup script to create the necessary directory structure and configuration files.

```bash
python setup.py
```
Follow the on-screen instructions to set up your .env file with your Venice API key.

### 2. Run a Workflow
The framework comes with a pre-built workflow to demonstrate its capabilities. You can run it using the run_symphony.py script.

```bash
# Run the default research and logging workflow
python run_symphony.py research_and_log

# See a list of all available workflows
python run_symphony.py
```
### 3. Check the Logs

Symphony uses clean, file-based logging. You can find the structured JSON logs for each component in the logs/ directory.

```bash
# View the log for the agent
tail -f logs/agent_v12_the_shell.log
```

### **Architecture Overview**

```markdown
## Architecture

### The Core (`symphony/`)

The `symphony/` package is the heart of the framework.

-   **`conductor.py`**: The central orchestrator that executes workflows.
-   **`agent_shell.py`**: The base class for all v12 agents.
-   **`agent_registry.py`**: Discovers and manages agent personas.
-   **`tool_registry.py`**: Discovers and manages tool classes.
-   **`tool.py`**: Defines the `SymphonyTool` base class.

### Components

-   **Agents (`agents/`)**: This directory contains all available agents. Each agent is a "doer" with its own persona configuration. The `agent_v12_the_shell` is the foundational agent.
-   **Tools (`symphony_tools/`)**: This directory contains all tools built on the Symphony standard, such as the `simple_file_system_tool` and `summarizer_tool`.
-   **Workflows (`workflows/`)**: This directory contains YAML files that define multi-step workflows, like `research_and_log.yaml`.
```

## Developer Guide

### Creating a New Tool

1.  Create a new file in `symphony_tools/` (e.g., `my_tool.py`).
2.  Inherit from the `SymphonyTool` base class.
3.  Implement the required methods (`.name`, `.description`, `.run()`, etc.).
4.  The `ToolRegistry` will automatically discover it.

### Creating a New Agent

1.  Create a new directory in `agents/` (e.g., `my_agent/`).
2.  Create a `config.json` defining its persona and default tools.
3.  Create your agent's Python script, inheriting from `AgentShell`.
4.  Run `python setup.py` to register it.

### Defining a Workflow

Create a new `.yaml` file in the `workflows/` directory. See `research_and_log.yaml` for an example of how to define a sequence of steps.

## Project Status

This is the v2.0.0 release of Project Symphony. The core architecture is stable and ready for development. The next phases will focus on expanding the library of agents and tools.