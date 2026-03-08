# Agents Orchestration & LangGraph Workflow

This document describes the multi-agent system architecture used in the **Gemelo Cognitivo** project. We use **LangGraph** to coordinate specialized AI agents in a robust, state-managed pipeline.

## 1. Architecture Overview
The system follows a sequential Directed Acyclic Graph (DAG) pattern. Each step in the process is a "Node" that operates on a shared "State".

### Core Components
- **State (`agents/state.py`):** A global `TypedDict` that acts as the "shared suitcase" carrying user data, AI results, courses, and error logs.
- **Orchestrator (`agents/graph.py`):** The engine that defines the flow, handles transitions, and compiles the execution logic.
- **Nodes (`agents/nodes/`):** Individual workers that contain the business logic and LLM calls.

---

## 2. The 4-Stage Pipeline

### Node 1: Profiler (`profiling_node.py`)
- **Role:** Analyzes raw questionnaire answers.
- **LLM:** Llama 3.1 8B (via Groq).
- **Output:** Structured competency levels mapped to our official taxonomy.
- **Guardrail:** Validates output against `CompetencyProfile` schema.

### Node 2: Retriever (`retriever.py`)
- **Role:** Acts as the RAG engine.
- **Logic:** Identifies "low level" competency gaps and performs semantic search in ChromaDB.
- **Output:** A list of relevant course metadata.

### Node 3: Planner (`planning_node.py`)
- **Role:** Designs the learning journey.
- **Logic:** Organizes courses into logical, ordered phases (Foundations, Advanced, etc.).
- **Output:** A structured `RoadmapStructure` JSON.

### Node 4: Explainer (`explanatory_node.py`)
- **Role:** Personalization and motivation.
- **Logic:** Writes detailed justifications in Spanish for each course based on the user's personal context.
- **Output:** The final, customer-ready Roadmap.

---

## 3. Security & Robustness (Guardrails)
We maintain a separation of concerns by placing safety logic in `agents/utils/guardrails.py`:
- **Schema Validation:** Every agent output is forced into a Pydantic model.
- **Error Handling:** Centralized management of LLM parsing failures and API timeouts.
- **State Logs:** Errors are recorded in the `errors` list of the state, allowing external nodes to decide whether to stop the flow.

## 4. Folder Structure
```text
agents/
├── data/           # Official taxonomies
├── nodes/          # Agent logic (The Workers)
├── prompts/        # Externalized LLM instructions
├── schemas/        # Pydantic data contracts
├── utils/           # Shared guardrails and tools
├── graph.py        # Pipeline orchestrator
└── state.py        # Global data structure
```
