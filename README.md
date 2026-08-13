# Enterprise Root-Cause & Decision Intelligence System (ERDIS)

## Dashboard Demo

The ERDIS Streamlit portfolio dashboard provides an interactive overview of multi-agent root-cause reasoning:

- **Executive Decision Summary**: Concise high-level operational analysis and recommendations.
- **Agent/Node Execution Trajectory**: Step-by-step visibility into cyclic LangGraph state transitions.
- **SQL & Document Evidence**: Ground-truth operational database queries and SLA contract excerpts.
- **Root-Cause Findings & Financial Impact**: Deconstructed operational failures paired with quantified financial impact.
- **Critic & Audit Results**: Adversarial verification identifying model assumptions vs. verified hard facts.
- **Human-in-the-Loop (HITL) Approval State**: Interactive risk threshold interrupts for executive review.
- **Citations & Assumptions**: Explicit separation of evidence sources from model inferences.
- **Deterministic Demo Mode**: Runs standalone out-of-the-box without requiring active PostgreSQL, Qdrant, FastAPI, or OpenAI credentials, while seamlessly connecting to the ERDIS FastAPI backend service when online.

### Running the Local Dashboard

From the project root:

```bash
.\venv\Scripts\activate
streamlit run app/dashboard.py
```

Then open:
http://localhost:8501
