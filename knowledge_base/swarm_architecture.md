# AI Swarm Platform Architecture

## Core Concepts
- **SwarmState**: Shared state dictionary tracking task inputs, research findings, code outputs, test results, iteration counters, and review feedback.
- **Dynamic Task Classifier**: Analyzes incoming tasks and determines the optimal execution workflow (`doc_only`, `code_only`, `testing_analysis`, `research_explanation`, `full_software`).
- **Self-Correction Loop**: Coder Agent and Tester Agent iterate up to a maximum of 3 times to fix syntax errors or logic bugs before proceeding.
- **Specialized Agents**: Planner, Researcher (RAG), Coder, Tester, Reviewer, and Documentation agents each perform focused roles.
