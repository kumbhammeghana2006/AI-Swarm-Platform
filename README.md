# AI-Swarm-Platform

Autonomous Multi-Agent AI Task-Solving Platform with Dynamic Orchestration, Knowledge Retrieval, and Iterative Self-Correction.

---

## 1. Research Contribution & Project Goal

The primary research objective of this platform is to empirically investigate:

> *"Does dynamic multi-agent orchestration, knowledge retrieval, and iterative self-correction improve task-solving performance compared with simpler configurations?"*

To evaluate this hypothesis, the platform tracks and aggregates empirical metrics for every executed task, enabling quantitative comparison between orchestrations and controlled ablation benchmarks.

---

## 2. System Architecture

```text
User
  ↓
React Frontend (Vite + Vanilla CSS)
  ↓
FastAPI Backend (REST API + JWT Bearer Auth)
  ↓
SQLAlchemy (SQLite / PostgreSQL Persistence)
  ↓
LangGraph Engine
  ↓
Coordinator / Task Classifier
  ↓
Dynamic Agent Routing (doc_only | code_only | testing_analysis | research_explanation | full_software)
  ↓
Planner / Researcher / RAG / Coder / Tester / Reviewer / Documentation
  ↓
Tester FAIL → Coder → Tester (Iterative Self-Correction Loop, capped at 3 iterations)
  ↓
Reviewer
  ↓
Documentation
  ↓
Consolidated Final Result & Metrics Storage
  ↓
React UI (Task Result, History & Evaluation Metrics Dashboard)
```

---

## 3. Dynamic Agent Routing

Instead of running a monolithic pipeline, the Coordinator Agent dynamically classifies incoming tasks into specialized routing topologies:
- **`doc_only`**: Classifier → Researcher → Documentation → Output
- **`code_only`**: Classifier → Planner → Coder ↔ Tester → Reviewer → Documentation → Output
- **`testing_analysis`**: Classifier → Tester → Output
- **`research_explanation`**: Classifier → Researcher → Documentation → Output
- **`full_software`**: Classifier → Planner → Researcher → Coder ↔ Tester → Reviewer → Documentation → Output

Agents are executed only when their specialized role is required. The `agents_used` list precisely reflects only the agents that participated in the execution.

---

## 4. Local Okapi BM25 RAG Pipeline

The RAG engine (`agents/rag_engine.py`) operates entirely locally without requiring heavy external vector database infrastructure:
1. **Document Loading**: Ingests markdown and text documents from `knowledge_base/`.
2. **Block Chunking**: Partitions documents into paragraph-level semantic blocks.
3. **Text Normalization**: Tokenizes into normalized word sequences.
4. **Okapi BM25 Scoring**: Calculates term frequency ($tf$), inverse document frequency ($idf$), and document-length normalized relevance scores.
5. **Top-K Retrieval**: Extracts top-$k$ relevant chunks and passes structured context with relevance scores to Researcher, Coder, and Documentation agents.

---

## 5. Iterative Self-Correction Loop

When code is generated, the Tester Agent validates it:
1. **Syntax Verification**: Uses Python's `ast` parser to verify syntax statically.
2. **Logical Verification**: Evaluates code against requirements and edge cases.
3. **Tester FAIL Routing**: If tests fail and the iteration count is under 3, the graph branches back to Coder Agent.
4. **Contextual Patching**: Coder receives:
   - Original task description
   - Previous code attempt
   - Exact tester failure diagnostic and feedback
   - Relevant RAG context
   - Execution plan
5. **Iteration Bound**: The loop is capped at a maximum of 3 iterations to guarantee termination.

---

## 6. Evaluation Metrics & Stored Data

For every swarm task, the database records:
- `task_id`: Unique identifier
- `task_type`: Resolved classification
- `execution_status`: `"SUCCESS"` or `"FAILED"`
- `configuration_type`: `"multi_agent"` (default active)
- `execution_time_seconds`: Wall-clock execution time
- `iteration_count`: Number of self-correction iterations executed
- `tester_result`: `"PASS"`, `"FAIL"`, or `"N/A"`
- `agents_used`: List of agents that actually executed
- `created_at`: UTC timestamp
- `task_text`: Input prompt
- `final_output`: Consolidated output or structured failure diagnostics

---

## 7. Metrics Aggregation & API

Empirical metrics are calculated dynamically via `backend/services/metrics_service.py` and exposed via protected endpoints:
- `GET /tasks/metrics/summary`: Returns metrics scoped to the authenticated user. If requested by an `ADMIN`, returns global system-wide metrics.
- `GET /admin/metrics/summary`: Admin-only endpoint returning system-wide metrics across all users.
- `GET /tasks/experiments/configurations`: Returns registered experiment and ablation configurations.

Calculated metrics include:
- Total tasks, successful tasks, failed tasks
- Success rate (`successful / total * 100`)
- Average execution time (seconds)
- Average iteration count
- Tester PASS rate and FAIL rate
- Agent usage frequency
- Task-type distribution
- Configuration distribution

---

## 8. Experiment & Ablation Support

The platform includes a formal experiment configuration registry (`backend/experiments/ablation.py`):
1. **`multi_agent_full`** (*Active/Default*): Multi-agent swarm with BM25 RAG and iterative self-correction.
2. **`multi_agent_no_rag`** (*Planned Ablation*): Multi-agent swarm without RAG context retrieval.
3. **`multi_agent_no_correction`** (*Planned Ablation*): Multi-agent swarm without self-correction loop.
4. **`single_agent_baseline`** (*Planned Baseline*): Single LLM agent baseline without multi-agent dynamic routing or iterative self-correction.

> **Important**:
> *"Single-agent execution is reserved for future controlled benchmarking and is not currently executable."*
> Submitting a task with `configuration_type="single_agent"` is rejected with HTTP 422 validation error, preventing fake single-agent execution or unverified data creation.

---

## 9. Running and Testing

### Backend Tests
Activate Python environment and run pytest:
```bash
.\venv\Scripts\pytest
```

### Frontend Development & Build
In the `frontend/` directory:
```bash
# Run lint check
npm run lint

# Build production bundle
npm run build

# Start local dev server
npm run dev
```

### Running Backend Server
```bash
uvicorn backend.main:app --reload --port 8000
```
