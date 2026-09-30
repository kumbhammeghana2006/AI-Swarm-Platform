# Agent Self-Correction and Iterative Refinement Guide

## Concept
Iterative self-correction enables an autonomous agent swarm to detect mistakes, ingest failure diagnostics, and regenerate solutions without human intervention. In software generation workflows, this manifests as an automated Tester-Coder feedback loop.

## The Tester -> Coder Feedback Loop
1. **Initial Code Generation**: CoderAgent generates an initial implementation from task requirements, architectural plan, and retrieved RAG context.
2. **Automated Verification**: TesterAgent verifies syntax with Python AST and evaluates logical correctness against task specifications.
3. **Outcome Branching**:
   - If tests **PASS**: The swarm advances to ReviewerAgent for code review and DocumentationAgent for documentation generation.
   - If tests **FAIL**: TesterAgent generates structured failure feedback, which is routed directly back to CoderAgent.
4. **Contextual Patching**: CoderAgent receives:
   - Original task description
   - Previous code attempt
   - Test results and failure diagnostic
   - Relevant knowledge base and RAG context
   CoderAgent applies targeted patches to address the exact failure points.
5. **Iteration Bound**: To prevent infinite loops and bound resource consumption, iterations are strictly capped (default: maximum 3 iterations). If max iterations are reached without passing, the latest code and diagnostic notes are forwarded to ReviewerAgent.
