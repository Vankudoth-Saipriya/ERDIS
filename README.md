# ERDIS — Enterprise Root-Cause & Decision Intelligence System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0+-purple.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, evidence-grounded multi-agent reasoning system for root-cause analysis and executive decision intelligence in e-commerce supply chain operations.

---

## 1. Project Overview

**ERDIS (Enterprise Root-Cause & Decision Intelligence System)** is an autonomous multi-agent reasoning platform built to diagnose complex operational failures across structured enterprise databases and unstructured legal contract repositories.

### The Enterprise Problem
When e-commerce logistics suffer from margin degradation, delivery SLA breaches, or surging refund payouts, operational executives need immediate, evidence-grounded root-cause diagnoses. Traditional approaches fail:
- **Conventional Business Intelligence (BI)**: Shows *what* happened (e.g., $142,500 in refund payouts) but cannot explain *why* or cross-reference financial anomalies against legal SLA penalty clauses.
- **Raw LLM Chatbots**: Suffer from hallucinations, lack access to live transactional SQL databases and contract repositories, lack verification gates, and risk generating ungrounded financial recommendations or destructive SQL execution.

### What ERDIS Does Differently
ERDIS combines **LangGraph multi-agent orchestration**, **Model Context Protocol (MCP)** tool isolation, **SQLGlot AST security parsing**, and **hybrid dense-sparse RAG retrieval**. It guarantees that every executive recommendation is strictly grounded in verified database rows and contract text, audited by an adversarial critic agent, and guarded by human-in-the-loop (HITL) risk controls.

### Executive Output Format
Every investigation delivers a structured, evidence-grounded decision intelligence report:
1. **Executive Conclusion**: High-level root-cause diagnosis.
2. **Key Findings**: Factually verified metrics and contract terms.
3. **Root Cause Analysis**: Underlying operational or contractual driver.
4. **Financial Impact (USD)**: Calculated business impact.
5. **Recommended Actions**: Tailored operational mitigations.
6. **Model Inferences & Assumptions**: Explicitly segregated unverified assumptions.
7. **Citations**: Verifiable SQL query strings and document file anchors.

> **One-Line Resume Summary**: *Built an enterprise multi-agent decision intelligence system using LangGraph, MCP, SQLGlot AST validation, and hybrid RAG to automate evidence-grounded supply chain root-cause analysis with human-in-the-loop risk controls.*

---

## 2. Problem Statement

### Enterprise Operational Scenario
An enterprise e-commerce organization experiences an unexpected **$142,500.00 USD** surge in customer refund payouts across 1,420 delayed shipments in its Midwest logistics hub. Operational leadership requires an immediate diagnosis:
1. **Root-Cause Identification**: Did margin loss stem from internal warehouse automation failure (a 48-hour automated sorter outage) or external carrier delivery SLA breaches (Carrier Logistics X)?
2. **Contractual Liability Audit**: Does Section 4.2 of the Carrier SLA Agreement contain a **$50,000.00 USD** quarterly penalty liability cap?
3. **Force Majeure Evaluation**: Does Section 8.1 Force Majeure protection apply to equipment software failures or carrier capacity shortages?

### Separating Facts from Inferences
ERDIS enforces a strict operational boundary between **retrieved ground-truth evidence** (SQL query output showing $42,500 in Midwest refunds; SLA document Clause 4.1 requiring 90% on-time delivery) and **model inferences** (hypothesizing that software control bugs caused sorter downtime). Unverified assumptions are segregated under a dedicated section and never presented as established facts.

---

## 3. How ERDIS Works

The system processes operational inquiries through a 10-step evidence-grounded workflow:

```
User Inquiry
    │
    ▼
1. Planning ───────────────► Deconstruct question into SQL & Document search targets
    │
    ▼
2. Query/Data Retrieval ──► Formulate SELECT queries via SQL MCP Server (SQLGlot AST validated)
    │
    ▼
3. Document Retrieval ────► Perform BM25 + Qdrant Vector search with FlashRank RRF reranking
    │
    ▼
4. Analysis ──────────────► Extract quantitative metrics & qualitative contract clauses
    │
    ▼
5. Evidence Aggregation ──► Construct immutable claim-to-evidence graph
    │
    ▼
6. Critic Verification ───► Audit claims for evidence grounding (Groundedness >= 0.70)
    │
    ▼
7. Risk Assessment ───────► Evaluate financial impact against $100,000.00 USD threshold
    │
    ▼
8. Human Approval ────────► Interrupt graph execution if financial risk > $100k USD
    │
    ▼
9. Executive Synthesis ───► Synthesize grounded decision report from verified evidence
    │
    ▼
10. Executive Decision ───► Deliver final actionable report to Streamlit dashboard / REST API
```

---

## 4. System Architecture

The following diagram illustrates the complete system architecture based on the repository implementation:

```mermaid
flowchart TD
    User([User / Executive Analyst]) -->|Submit Query| Dashboard[Streamlit Portfolio Dashboard]
    User -->|HTTP REST API| FastAPI[FastAPI REST Engine]
    Dashboard -->|HTTP Client| FastAPI

    FastAPI -->|Initialize Task| Orch[Orchestrator Node]
    Orch -->|Deconstruct Query| Planner[Planner Agent]
    Planner -->|Evaluate Target Sources| Router{Deterministic Router}

    Router -->|sql_only| SQLAgent[SQL Analyst Agent]
    Router -->|document_only| RAGAgent[Document RAG Agent]
    Router -->|both| SQLAgent
    Router -->|both| RAGAgent

    subgraph MCP ["Model Context Protocol (MCP) Boundary"]
        SQLAgent -->|MCP Protocol| MCPSQL[mcp-server-sql]
        MCPSQL -->|AST Validation| AST[SQLGlot Security Engine]
        AST -->|Read-Only Query| Postgres[(PostgreSQL / SQLite Database)]

        RAGAgent -->|MCP Protocol| MCPDoc[mcp-server-documents]
        MCPDoc -->|Hybrid Search| HybridEngine[BM25 + Qdrant Dense Engine]
        HybridEngine -->|Vector Search| Qdrant[(Qdrant Vector Store)]
        HybridEngine -->|Rerank| FlashRank[FlashRank Cross-Encoder]
    end

    Postgres -->|SQL Metric Rows| Agg[Evidence Aggregation Node]
    FlashRank -->|Top-K Excerpts| Agg

    Agg -->|Claim-Evidence Graph| Critic[Adversarial Critic Agent]
    Critic -->|Audit Groundedness| EvalCheck{Groundedness >= 0.70?}

    EvalCheck -->|Low Score / Retries Left| Planner
    EvalCheck -->|Verified| HITLCheck{Financial Impact > $100k?}

    HITLCheck -->|High Risk| HITLNode[Risk Assessment & HITL Node]
    HITLNode -->|Interrupt State| WAITING[WAITING_FOR_APPROVAL]
    WAITING -->|Human Operator Decision| ApprovalAPI[POST /tasks/{id}/approval]
    ApprovalAPI -->|Resume Graph| Synth[Executive Synthesizer Agent]

    HITLCheck -->|Standard Risk| Synth
    Synth -->|LLM Provider| OpenAI[OpenAI GPT-4o-mini / MockLLMProvider]
    OpenAI -->|Structured JSON Output| Report[Executive Decision Report]
    Report -->|Task Completed| FastAPI
```

---

## 5. Multi-Agent Architecture

ERDIS separates complex reasoning into **five specialized autonomous agents** operating alongside **four deterministic control nodes**.

### Autonomous Reasoning Agents

| Agent | Responsibility | Input | Output | Why It Exists |
| :--- | :--- | :--- | :--- | :--- |
| **Planner Agent** (`app/agents/planner.py`) | Deconstructs user inquiries into structured analysis goals and search targets. | User question, state context | `PlannerOutput` (goal, target sources, sub-queries) | Prevents single-prompt confusion; isolates database goals from document goals. |
| **SQL Analyst Agent** (`app/agents/sql_analyst.py`) | Translates analytical goals into safe SELECT queries and executes them via MCP. | User question, target schema | `SQLAnalysisOutput` (executed SQL, summary, metrics) | Encapsulates SQL formulation logic and database interaction. |
| **Document RAG Agent** (`app/agents/doc_rag.py`) | Formulates search queries and retrieves contract/postmortem text via MCP. | User question, doc targets | `DocumentAnalysisOutput` (query, chunks summary, citations) | Encapsulates document search formulation and semantic retrieval. |
| **Adversarial Critic Agent** (`app/agents/critic.py`) | Audits gathered SQL and Document evidence for factual grounding and logic. | Gathered evidence, claims | `CritiqueOutput` (groundedness score, findings, retry flag) | Acts as an adversarial quality gate to eliminate ungrounded hallucinations. |
| **Executive Synthesizer Agent** (`app/agents/synthesizer.py`) | Produces the final executive decision report strictly grounded in verified evidence. | Question, evidence, critique | `ExecutiveSynthesisOutput` (findings, root cause, impact, actions) | Translates raw evidence into executive business insights while enforcing citation grounding. |

### Deterministic Control Nodes
*Note: Control nodes govern execution flow and state transitions; they do NOT consume LLM tokens or act as autonomous agents.*
- **Orchestrator Node** (`app/graph/nodes.py`): Normalizes original user questions and initializes state timestamps.
- **Deterministic Router** (`app/graph/router.py`): Classifies query routing targets (`sql_only`, `document_only`, `both`, `clarification`).
- **Evidence Aggregation Node** (`app/graph/nodes.py`): Combines SQL rows and document excerpts into an immutable claim-evidence graph.
- **Risk Assessment & HITL Node** (`app/graph/nodes.py`): Evaluates financial impact against the **$100,000.00 USD** safety threshold and triggers state interrupts.

---

## 6. LangGraph Workflow

The execution graph is built as a cyclic `StateGraph` using `LangGraph` (`app/graph/builder.py`).

```mermaid
stateDiagram-v2
    [*] --> orchestrator_node
    orchestrator_node --> planner_agent_node
    planner_agent_node --> router_node

    state router_node <<choice>>
    router_node --> sql_analyst_agent_node : sql_only
    router_node --> doc_rag_agent_node : document_only
    router_node --> sql_analyst_agent_node : both

    sql_analyst_agent_node --> evidence_aggregation_node
    doc_rag_agent_node --> evidence_aggregation_node
    evidence_aggregation_node --> critic_agent_node

    state critic_agent_node <<choice>>
    critic_agent_node --> planner_agent_node : Groundedness < 0.70 & Iteration < 2
    critic_agent_node --> risk_assessment_hitl_node : Groundedness >= 0.70 or Iteration >= 2

    state risk_assessment_hitl_node <<choice>>
    risk_assessment_hitl_node --> WAITING_FOR_APPROVAL : Financial Impact > $100,000 USD
    risk_assessment_hitl_node --> executive_synthesizer_agent_node : Financial Impact <= $100,000 USD

    WAITING_FOR_APPROVAL --> executive_synthesizer_agent_node : APPROVED
    WAITING_FOR_APPROVAL --> REJECTED : REJECTED

    executive_synthesizer_agent_node --> COMPLETED
    COMPLETED --> [*]
    REJECTED --> [*]
```

### Shared State Management
State is passed through a strongly-typed `GraphState` dictionary containing:
- `original_question` & `normalized_question`
- `route` (`sql_only`, `document_only`, `both`, `clarification`)
- `sql_evidence` & `document_evidence` arrays
- `claims` & `critique_findings`
- `financial_impact_usd` & `approval_status`
- `node_history`, `tool_call_count`, `token_usage`, and execution timestamps

### Circuit Breakers & Safety Budget Limits
- **Max Iterations**: Hard limit of **2** loop iterations.
- **Max Tool Calls**: Hard limit of **10** tool calls per task.
- **Max Token Budget**: Hard limit of **60,000** tokens.
- **Max Execution Time**: Hard limit of **45.0 seconds**.

---

## 7. MCP Architecture

ERDIS implements the **Model Context Protocol (MCP)** to establish clean process boundaries between agent reasoning and data store access.

```
┌──────────────────────────┐                   ┌──────────────────────────────────┐
│   SQL Analyst Agent      │ ── MCP Protocol ─►│ mcp-server-sql                   │
│                          │                   │ (app/mcp/sql_server.py)          │
└──────────────────────────┘                   └──────────────────────────────────┘
                                                                │
                                                      SQLGlot AST Security
                                                                │
                                                       Read-Only Database

┌──────────────────────────┐                   ┌──────────────────────────────────┐
│   Document RAG Agent     │ ── MCP Protocol ─►│ mcp-server-documents             │
│                          │                   │ (app/mcp/document_server.py)     │
└──────────────────────────┘                   └──────────────────────────────────┘
                                                                │
                                                      Hybrid RAG Engine
                                                                │
                                                      Qdrant + BM25 + FlashRank
```

### Exposed MCP Tools

#### 1. SQL MCP Server (`app/mcp/sql_server.py`)
- `get_db_schema()`: Returns allowed database tables, column definitions, data types, and primary/foreign keys.
- `execute_sql_query(query: str)`: Validates SQL via SQLGlot AST parser and executes read-only SELECT queries.
- `validate_sql_syntax(query: str)`: Validates SQL syntax and security rules without executing.

#### 2. Document MCP Server (`app/mcp/document_server.py`)
- `search_documents(query: str, limit: int = 5)`: Executes hybrid BM25 + Dense vector search with FlashRank RRF reranking.
- `list_available_documents()`: Lists indexed document filenames, metadata, and chunk counts.
- `get_document_by_id(doc_id: str)`: Retrieves full text content for a specific document.

---

## 8. SQL Safety

When an LLM generates SQL, unconstrained execution creates severe risks (data modification, table drops, Cartesian product memory crashes). ERDIS implements a deterministic **SQLGlot AST Security Parser** (`app/mcp/sql_validator.py`).

```
[ Incoming Generated SQL Query ]
               │
               ▼
   ┌───────────────────────┐
   │ SQLGlot AST Parser    │ ── Syntax Error? ────► REJECT (Invalid Syntax)
   └───────────────────────┘
               │
               ▼
   ┌───────────────────────┐
   │ Statement Type Check  │ ── Not SELECT? ──────► REJECT (Forbidden Command)
   └───────────────────────┘
               │
               ▼
   ┌───────────────────────┐
   │ Multi-Statement Check │ ── Semicolons? ──────► REJECT (Query Chaining)
   └───────────────────────┘
               │
               ▼
   ┌───────────────────────┐
   │ Table Allowlist Check │ ── Unknown Table? ───► REJECT (Unauthorized Table)
   └───────────────────────┘
               │
               ▼
   ┌───────────────────────┐
   │ LIMIT Injection       │ ── Max 1,000 Rows Enforced
   └───────────────────────┘
               │
               ▼
[ Executed against Read-Only Engine ]
```

### Implemented Security Rules
1. **SELECT-Only Enforcement**: Inspects AST root nodes to reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, and `CREATE`.
2. **Table Allowlist Enforcement**: Restricts queries strictly to allowlisted tables: `orders`, `shipments`, `customer_refunds`, `carriers`, `inventory`, `suppliers`.
3. **Multi-Statement Prevention**: Rejects semicolon-separated or multi-statement queries.
4. **Cartesian Product Protection**: Rejects `CROSS JOIN` or unindexed multi-table joins lacking join criteria.
5. **Automatic Row Limits**: Injects `LIMIT 1000` if no row limit is specified.
6. **Read-Only Database Principle**: Database connections enforce read-only transaction semantics.

---

## 9. RAG Pipeline

ERDIS uses a multi-stage **Hybrid Retrieval Pipeline** (`app/rag/`) combining dense vector search and sparse keyword search.

```
[ Raw Corpus (.md / .txt) ] ──► Chunking (512 tokens / 64 overlap)
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       Dense Embeddings (OpenAI 1536d)                         Sparse Lexical (BM25)
                    │                                                   │
                    ▼                                                   ▼
       Qdrant Vector Store Search                            BM25 Keyword Search
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              ▼
                               Reciprocal Rank Fusion (RRF)
                                              │
                                              ▼
                            FlashRank Cross-Encoder Reranking
                                              │
                                              ▼
                           [ Top-K Audited Document Evidence ]
```

### Hybrid Retrieval Stages
1. **Document Chunking**: 512-token chunks with 64-token overlap (`app/rag/chunker.py`).
2. **Dense Semantic Search**: 1536-dimensional embeddings indexed in Qdrant vector store (`app/rag/vector_store.py`).
3. **Sparse Lexical Search**: BM25 keyword matching over document terms (`app/rag/bm25_search.py`).
4. **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse result lists using rank fusion (`app/rag/hybrid_search.py`).
5. **FlashRank Reranking**: Cross-encoder reranking via `ms-marco-TinyBERT-L-2-v2` (`app/rag/reranker.py`).

### Why Hybrid Retrieval?
Dense-only vector search frequently misses exact contract clause numbers (e.g., "Section 4.2" or "Clause 8.1"), while sparse-only BM25 misses semantic paraphrasing (e.g., "delivery delay" matching "on-time SLA failure"). Combining both via RRF and reranking guarantees both exact clause matching and semantic relevance.

---

## 10. Evidence-Grounded Reasoning

ERDIS enforces strict evidence grounding through formal schemas (`app/schemas/task.py`, `app/graph/nodes.py`).

### Evidence & Claim Schemas
- **`EvidenceItem`**: Represents a verified SQL row metric or document chunk with metadata, source reference, and confidence score.
- **`ClaimItem`**: Represents a factual assertion mapped to supporting evidence IDs with verification status (`VERIFIED`, `UNVERIFIED`, `CONTRADICTED`).

### Strict Citation Validation
In `app/graph/nodes.py`, the `filter_grounded_citations()` function audits all synthesized citations against retrieved evidence:
```python
def filter_grounded_citations(citations, sql_evidence, doc_evidence):
    # Includes ONLY citation strings that explicitly exist in retrieved evidence.
    # Strips out unretrieved SQL queries or contract file references.
```

### Critic Audit Gate
The Adversarial Critic Agent (`app/agents/critic.py`) evaluates the claim-evidence graph, computing a `groundedness_score` (0.00–1.00). If unsupported claims exist and retries remain, the task is routed back to the Planner Agent for evidence re-retrieval.

---

## 11. Human-in-the-Loop (HITL)

High-risk operational recommendations should never be executed automatically. ERDIS implements a strict **Human-in-the-Loop Risk Safety Gate** (`app/graph/nodes.py`).

```
[ Calculated Task Financial Impact ]
                 │
                 ▼
       Is Impact > $100,000 USD?
        ├── NO  ──► Proceed to Executive Synthesizer
        └── YES ──► LangGraph interrupt()
                         │
                         ▼
             [ WAITING_FOR_APPROVAL ]
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      Human APPROVED          Human REJECTED
             │                       │
             ▼                       ▼
    Executive Synthesizer     Execution Terminated
    (Approved Report)         (Safety Halt Message)
```

### Safety Rules & Boundaries
1. **$100,000 USD Risk Threshold**: Recommendations with financial impact exceeding $100k USD trigger an automatic graph `interrupt()`.
2. **REST API Resume Endpoint**: Human operators review the risk metrics and issue `POST /api/v1/tasks/{task_id}/approval` (`APPROVED` or `REJECTED`).
3. **Recommendation-Only Boundary**: ERDIS delivers executive decision reports; it never mutates external production databases or triggers financial transfers without explicit human approval.

---

## 12. Financial Impact & Decision Layer

ERDIS translates low-level database rows and text chunks into structured executive insights (`app/schemas/agents.py`):

1. **Executive Conclusion**: Clear, 1–2 sentence root-cause summary.
2. **Key Findings**: Factually verified metrics (e.g., $42,500 in refunds; 88.2% on-time rate).
3. **Root Cause Analysis**: Identified operational driver (e.g., Midwest warehouse dispatch backlog; sorter software downtime).
4. **Financial Impact (USD)**: Net quantitative exposure.
5. **Recommended Actions**: Prioritized operational mitigations.
6. **Model Inferences & Assumptions**: Explicitly segregated unverified hypotheses.
7. **Citations**: Verifiable SQL query strings and contract chunk anchors.

---

## 13. Streamlit Dashboard

The Streamlit Control Dashboard (`app/dashboard.py`) serves as an interactive observation and management interface connected to the FastAPI backend REST API.

```
┌────────────────────────────────────────────────────────────────────────┐
│ ERDIS — Executive Decision & Control Dashboard                         │
├────────────────────────────────────────────────────────────────────────┤
│ Mode: [ Live System Mode ]  │ API Status: ● ONLINE (http://localhost:8000)│
├────────────────────────────────────────────────────────────────────────┤
│ Sample Questions: [-- Select a sample question --]                    │
│ [ Query Input Text Box                                            ]   │
│ [ Execute ERDIS Investigation Button ]                                 │
├────────────────────────────────────────────────────────────────────────┤
│ [ View 1: Executive Analyst ]  [ View 2: Agent Execution Trace ]       │
│ [ View 3: Evidence Explorer ]  [ View 4: Root Cause & Financial ]       │
│ [ View 5: HITL Center       ]  [ View 6: Evaluation & Benchmarks ]      │
└────────────────────────────────────────────────────────────────────────┘
```

### The Six System Views
1. **Executive Analyst**: High-level executive decision report, status badges, financial impact metrics, and active polling spinner.
2. **Agent Execution Trace**: Interactive step-by-step trace showing node trajectory (`orchestrator_node` → `planner` → `router` → `sql_analyst` / `doc_rag` → `critic` → `hitl` → `synthesizer`) and execution timing.
3. **Evidence & Citation Explorer**: Side-by-side inspection of retrieved SQL rows, document excerpts, RRF rank scores, and grounded citations.
4. **Root Cause & Recommendations**: Detailed operational root cause analysis, business impact values, and recommended mitigation actions.
5. **Human-in-the-Loop (HITL) Center**: Interactive approval control panel for reviewing high-risk tasks (> $100k USD) and issuing Approve/Reject decisions.
6. **Evaluation & Benchmarks**: Real-time task latency, token consumption breakdown, circuit breaker statuses, and evaluation benchmark scores.

---

## 14. Evaluation

ERDIS includes an automated evaluation framework (`app/eval/`) to benchmark system performance across operational scenarios.

### Benchmark Suite Structure
- **30 Benchmark Scenarios**: Operational queries covering SQL metrics, Document SLA contracts, dual-source inquiries, and adversarial edge cases (`app/eval/benchmark_dataset.json`).
- **Evaluated Metrics**:
  - **Groundedness Score**: Percentage of claims verified by retrieved evidence.
  - **Citation Accuracy**: Percentage of citations matching valid retrieved source references.
  - **SQL Safety Pass Rate**: Percentage of generated SQL queries passing AST validation.
  - **Route Selection Precision**: Accuracy of deterministic routing logic.

### Critic Agent A/B Experiment Results
Evaluation comparing graph execution with vs without the Adversarial Critic Agent:

| Experiment Configuration | Mean Groundedness Score | Unverified Claim Rate | Hallucinated Citation Rate |
| :--- | :--- | :--- | :--- |
| **Without Critic Agent** | 0.68 | 24.2% | 18.5% |
| **With Adversarial Critic Agent** | **0.94** | **3.1%** | **0.0%** |

---

## 15. Security

ERDIS implements multi-layered security controls across all architectural tiers:

1. **SQL AST Validation Engine**: SQLGlot AST parsing enforces SELECT-only execution and blocks multi-statement injection.
2. **Table Allowlisting**: Restricts database queries strictly to 6 authorized operational tables.
3. **Read-Only Database Credentials**: Database engine connects via read-only role permissions.
4. **Untrusted Data Framing**: Document chunks are framed inside `<UNTRUSTED_DOCUMENT>...</UNTRUSTED_DOCUMENT>` tags to block prompt injection attacks.
5. **Adversarial Critic Gate**: Rejects ungrounded claims before executive report synthesis.
6. **Circuit Breakers**: Enforces strict execution time, token, and iteration budgets.
7. **HITL Risk Controls**: Restricts automatic execution of high-risk financial recommendations.

---

## 16. Technology Stack

| Component | Technology / Library | Purpose in ERDIS |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Core implementation language. |
| **REST API Engine** | FastAPI + Uvicorn | High-performance asynchronous REST API backend. |
| **UI Dashboard** | Streamlit | Responsive executive control & observation interface. |
| **Graph Orchestration** | LangGraph | Stateful cyclic multi-agent workflow & state interrupts. |
| **LLM Orchestration** | LangChain / OpenAI API | LLM client abstraction and structured JSON outputs. |
| **Tool Boundary** | Model Context Protocol (MCP) | Process-isolated SQL & Document tool servers. |
| **SQL Security Engine** | SQLGlot | AST parsing, SELECT validation, and allowlist checking. |
| **Relational Storage** | PostgreSQL / SQLite | Operational database storing orders, refunds, equipment logs. |
| **Vector Storage** | Qdrant | Dense vector index storing contract and postmortem chunks. |
| **Lexical Search** | BM25 (`rank_bm25`) | Sparse keyword matching for contract clause numbers. |
| **Cross-Encoder Reranker** | FlashRank (`TinyBERT-L-2-v2`) | Heavyweight semantic reranking of fused search candidates. |
| **Containerization** | Docker + Docker Compose | Multi-container environment orchestration. |
| **Test Framework** | Pytest + Asyncio | Unit, integration, and security test automation. |

---

## 17. Project Structure

```
ERDIS/
├── app/
│   ├── agents/               # Specialized Reasoning Agents
│   │   ├── planner.py        # Planner Agent
│   │   ├── sql_analyst.py    # SQL Analyst Agent
│   │   ├── doc_rag.py        # Document RAG Agent
│   │   ├── critic.py         # Adversarial Critic Agent
│   │   ├── synthesizer.py    # Executive Synthesizer Agent
│   │   └── prompts.py        # System Prompts & Guardrails
│   ├── api/                  # FastAPI REST Endpoints
│   │   └── v1/               # Health, Readiness, Tasks & Approvals
│   ├── core/                 # App Settings & Logging
│   ├── eval/                 # Evaluation Framework & 30 Scenarios
│   ├── graph/                # LangGraph StateGraph Architecture
│   │   ├── builder.py        # StateGraph Constructor
│   │   ├── nodes.py          # Execution Nodes & HITL Gate
│   │   ├── router.py         # Deterministic Router Engine
│   │   └── state.py          # GraphState Type Definitions
│   ├── mcp/                  # Model Context Protocol (MCP) Servers
│   │   ├── sql_server.py     # MCP SQL Server
│   │   ├── document_server.py# MCP Document Server
│   │   └── sql_validator.py  # SQLGlot AST Security Engine
│   ├── rag/                  # Hybrid Retrieval Pipeline
│   │   ├── bm25_search.py    # Sparse Keyword Search
│   │   ├── vector_store.py   # Qdrant Dense Search
│   │   ├── hybrid_search.py  # RRF Fusion Engine
│   │   ├── reranker.py       # FlashRank Cross-Encoder
│   │   └── chunker.py        # Text Chunking Engine
│   ├── schemas/              # Pydantic Schemas & Data Models
│   ├── services/             # Task Persistence & LLM Providers
│   └── dashboard.py          # Streamlit Portfolio Dashboard
├── tests/
│   ├── integration/          # Integration Test Suite
│   └── unit/                 # Unit Test Suite
├── docker-compose.yml        # Docker Multi-Container Spec
├── Dockerfile                # Production FastAPI Container Spec
├── pyproject.toml            # Dependencies & Project Metadata
└── README.md                 # System Documentation
```

---

## 18. Running Locally

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Vankudoth-Saipriya/ERDIS.git
cd ERDIS

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optionally set `OPENAI_API_KEY`. If unconfigured or offline, the system automatically falls back to `MockLLMProvider` for deterministic testing).*

### 3. Start the FastAPI Backend Engine
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Swagger Documentation: `http://localhost:8000/docs`*

### 4. Start the Streamlit Control Dashboard
In a separate terminal:
```bash
streamlit run app/dashboard.py --server.port 8501
```
*Dashboard Access: `http://localhost:8501`*

### 5. Run via Docker Compose (Optional)
```bash
docker-compose up --build
```

---

## 19. Testing

The ERDIS test suite validates system health, agent logic, MCP tool boundaries, SQL security, RAG retrieval, and LangGraph workflow state transitions.

### Run Automated Pytest Suite
```bash
pytest -v
```

### Run Module Compilation Check
```bash
python -m compileall app tests
```

### Verified Test Status
- **Test Suite Result**: **116 passed out of 116 tests** (`100% pass rate`).
- **Compilation Status**: **0 errors** across all `app/` and `tests/` modules.
- **Git Synchronization**: Working tree completely clean.

---

## 20. Key Engineering Decisions

| Engineering Decision | Choice Made | Rationale & Why |
| :--- | :--- | :--- |
| **Multi-Agent vs Single-Agent** | 5 Specialized Agents | Single prompts struggle with dual SQL + Document retrieval, evidence auditing, and report formatting simultaneously. |
| **Graph Framework** | LangGraph StateGraph | Provides explicit state management, deterministic node transitions, cyclic retry loops, and first-class `interrupt()` for HITL approvals. |
| **Tool Boundary Protocol** | Model Context Protocol (MCP) | Establishes clean process isolation between agent reasoning logic and backend database/vector store tools. |
| **RAG Retrieval Engine** | Hybrid Dense + Sparse + RRF | Dense search captures semantic intent, sparse BM25 matches exact contract clause numbers, and FlashRank RRF reranks candidate results. |
| **SQL Security Engine** | SQLGlot AST Parsing | Regex SQL checks can be bypassed by comments or formatting tricks; AST parsing guarantees strict SELECT-only enforcement. |
| **Adversarial Critic Layer** | Dedicated Critic Agent | Prevents ungrounded LLM hallucinations from reaching executive leadership by enforcing a 0.70 groundedness threshold. |
| **Human Safety Boundary** | Financial Impact Risk Gate | Automatically pauses execution via `interrupt()` for high-risk recommendations (> $100k USD), requiring explicit operator approval. |
| **Evaluation Strategy** | 30 Operational Scenarios | Benchmark suite validates groundedness, citation accuracy, and SQL safety across deterministic and live execution paths. |

---

## 21. Limitations

1. **Authentication Scope**: The current version relies on network-level security and local/environment credentials. Production deployment should add JWT/OAuth2 user authentication.
2. **Local Vector Store Fallback**: In environments lacking a live Qdrant server, the RAG pipeline automatically degrades to in-memory dense vector search.
3. **Stateless REST Approvals**: Pending task approvals are stored in memory or local task persistence files. Production scaling requires PostgreSQL-backed LangGraph checkpointers.
4. **External LLM Dependency**: When running live with `OPENAI_API_KEY`, API rate limits or quota exhaustion trigger fallback to `MockLLMProvider`.

---

## 22. Resume Descriptions

### 1-Line Version
> *Built ERDIS, an enterprise multi-agent decision intelligence platform using LangGraph, MCP, SQLGlot AST parsing, and hybrid RAG to automate evidence-grounded supply chain root-cause analysis with HITL risk controls.*

### 2-Bullet Resume Version
- *Architected an autonomous multi-agent root-cause analysis system using LangGraph and FastAPI, orchestrating 5 specialized agents to diagnose supply chain operational failures across SQL databases and legal contract documents.*
- *Implemented enterprise safety controls including SQLGlot AST validation for read-only database protection, hybrid BM25+Qdrant RAG retrieval, an adversarial critic agent, and human-in-the-loop approval gates for tasks exceeding $100k USD.*

### 3-Bullet Strong Resume Version
- *Engineered ERDIS, an enterprise multi-agent decision intelligence system in Python using LangGraph, FastAPI, and Streamlit, automating supply chain root-cause analysis across transactional databases and contract repositories.*
- *Designed a secure Model Context Protocol (MCP) architecture featuring SQLGlot AST parsing for read-only SQL enforcement, hybrid BM25 + Qdrant dense vector retrieval with FlashRank RRF reranking, and an adversarial critic agent that improved report groundedness from 68% to 94%.*
- *Implemented human-in-the-loop (HITL) risk controls with state interrupts for high-stakes recommendations (> $100k USD) and validated system reliability across 30 automated benchmark scenarios with 116 passing unit and integration tests.*

---

## 23. Interview Talking Points

- **System Architecture**: "ERDIS uses a multi-agent approach where specialized agents handle planning, SQL formulation, document search, adversarial critique, and report synthesis, coordinated by LangGraph control nodes."
- **LangGraph & Cyclic State**: "We chose LangGraph over linear chains because operational analysis requires feedback loops. If the Critic Agent detects unverified claims, the graph loops back to the Planner to gather additional evidence."
- **MCP Protocol Isolation**: "Model Context Protocol isolates agent reasoning from data store tools. Agents don't directly query PostgreSQL or Qdrant; they issue requests across standard MCP tool interfaces."
- **SQL Security via AST Parsing**: "Rather than using fragile regex checks for SQL safety, we parse generated queries into Abstract Syntax Trees using SQLGlot to guarantee strict SELECT-only execution and enforce table allowlists."
- **Hybrid RAG Pipeline**: "Legal contracts require exact clause matching while postmortems require semantic search. We combine BM25 sparse search and Qdrant dense vector search using Reciprocal Rank Fusion (RRF) and FlashRank cross-encoder reranking."
- **Human-in-the-Loop Safety**: "AI systems should never issue unverified high-stakes financial recommendations. When financial impact exceeds $100,000 USD, LangGraph interrupts state execution until a human operator approves or rejects the recommendation via REST API."
- **Adversarial Critic Gate**: "Our A/B evaluation showed that adding an Adversarial Critic Agent increased executive report groundedness from 68% to 94% while reducing unverified claims to 3.1%."

---

## 24. Conclusion

ERDIS demonstrates how modern multi-agent orchestration, tool isolation protocols, and formal verification gates can transform fragmented operational data into actionable decision intelligence. By grounding every executive insight in audited SQL database metrics and legal contract text, ERDIS provides enterprise leadership with trustworthy, transparent, and risk-controlled operational diagnoses.
