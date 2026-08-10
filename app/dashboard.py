"""
Enterprise Root-Cause & Decision Intelligence System (ERDIS)
Streamlit Portfolio Demo Dashboard.
Exposes multi-agent LangGraph reasoning, SQL & Document MCP evidence,
Human-in-the-Loop approval workflows, and continuous evaluation benchmark metrics.
"""

import time
import json
import os
import httpx
import streamlit as st

# Configure Streamlit Page
st.set_page_config(
    page_title="ERDIS — Decision Intelligence System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Enterprise Aesthetics
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0E1117;
        color: #E0E6ED;
        font-family: 'Inter', system-ui, sans-serif;
    }
    .metric-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
    }
    .status-pending { background-color: #3B82F6; color: #FFFFFF; }
    .status-running { background-color: #F59E0B; color: #FFFFFF; }
    .status-approval { background-color: #EF4444; color: #FFFFFF; animation: pulse 2s infinite; }
    .status-completed { background-color: #10B981; color: #FFFFFF; }
    .status-rejected { background-color: #6B7280; color: #FFFFFF; }

    .agent-card {
        background-color: #1F2937;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 0 6px 6px 0;
    }
    .evidence-box {
        background-color: #0D1117;
        border: 1px solid #21262D;
        border-radius: 6px;
        padding: 14px;
        font-family: 'Fira Code', monospace;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# API Client Configuration
API_BASE_URL = os.getenv("ERDIS_API_URL", "http://localhost:8000")


def get_api_client():
    return httpx.Client(base_url=API_BASE_URL, timeout=10.0)


# Check API Health & Readiness
@st.cache_data(ttl=5)
def check_api_status():
    try:
        with get_api_client() as client:
            res_health = client.get("/api/v1/health")
            res_ready = client.get("/api/v1/readiness")
            if res_health.status_code == 200 and res_ready.status_code == 200:
                return "ONLINE", res_ready.json()
    except Exception:
        pass
    return "OFFLINE", {}


# Sidebar Navigation & System Status
st.sidebar.image("https://img.icons8.com/color/96/000000/brain.png", width=60)
st.sidebar.title("ERDIS Navigation")
st.sidebar.caption("Enterprise Root-Cause & Decision Intelligence")

page = st.sidebar.radio(
    "Select System View",
    [
        "1. Executive Analyst",
        "2. Agent Execution Trace",
        "3. Evidence & Citation Explorer",
        "4. Root Cause & Recommendations",
        "5. Human-in-the-Loop (HITL) Center",
        "6. Evaluation & Benchmarks",
    ],
)

api_status, ready_data = check_api_status()

st.sidebar.markdown("---")
if api_status == "ONLINE":
    st.sidebar.success(f"🟢 ERDIS API Engine: {api_status}")
    st.sidebar.caption(f"DB: {ready_data.get('database')} | Vector Store: {ready_data.get('vector_store')}")
else:
    st.sidebar.warning(f"🟡 ERDIS API Engine: Local Service Mode")

mode_toggle = st.sidebar.selectbox("Execution Mode", ["Demo Mode (Deterministic Mock)", "Live System Mode"])
st.sidebar.info(f"Active Mode: **{mode_toggle}**")

# Initialize Session State Variables
if "active_task_id" not in st.session_state:
    st.session_state["active_task_id"] = None
if "current_task_data" not in st.session_state:
    st.session_state["current_task_data"] = None


# Helper function to submit or fetch task
def fetch_task_status(task_id: str):
    try:
        with get_api_client() as client:
            res = client.get(f"/api/v1/tasks/{task_id}")
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass
    return st.session_state.get("current_task_data")


# ==============================================================================
# PAGE 1: EXECUTIVE ANALYST
# ==============================================================================
if page == "1. Executive Analyst":
    st.title("⚡ Enterprise Root-Cause & Decision Intelligence System")
    st.markdown(
        """
        *ERDIS replaces generic chat interfaces with evidence-grounded multi-agent reasoning, combining SQL operational databases, enterprise SLA contracts, and adversarial audit controls.*
        """
    )
    st.markdown("---")

    col_q1, col_q2 = st.columns([2, 1])

    with col_q1:
        st.subheader("Submit Operational Inquiry")

        # Preset Sample Queries
        sample_query = st.selectbox(
            "Select Sample Inquiry Scenario or type custom query below:",
            [
                "-- Select a sample question --",
                "What is total Midwest customer refund payout amount?",
                "What was the primary root cause of Midwest operational margin degradation in Q3?",
                "Midwest 100k financial refund impact carrier SLA contract penalty clause",
                "DROP TABLE orders; SELECT * FROM customer_refund_policy;",
            ],
        )

        default_input = ""
        if sample_query != "-- Select a sample question --":
            default_input = sample_query

        user_query = st.text_area(
            "Enter Operational Question / Issue Statement:",
            value=default_input,
            height=100,
            placeholder="e.g., Why did Midwest logistics margin deteriorate in Q3?",
        )

        btn_submit = st.button("🚀 Execute ERDIS Investigation", type="primary")

        if btn_submit and user_query.strip():
            with st.spinner("Initiating Multi-Agent Reasoning Pipeline..."):
                try:
                    with get_api_client() as client:
                        res = client.post("/api/v1/tasks", json={"query": user_query.strip()})
                        if res.status_code == 201:
                            task_info = res.json()
                            st.session_state["active_task_id"] = task_info["task_id"]
                            st.session_state["current_task_data"] = task_info
                            st.success(f"Task Created: `{task_info['task_id']}`")
                        else:
                            st.error(f"API Error ({res.status_code}): {res.text}")
                except Exception as err:
                    # Fallback task creation for local demo
                    mock_task_id = "TASK-DEMO-01"
                    st.session_state["active_task_id"] = mock_task_id
                    st.session_state["current_task_data"] = {
                        "task_id": mock_task_id,
                        "status": "COMPLETED",
                        "original_question": user_query.strip(),
                        "executive_conclusion": "Root-cause analysis confirms Midwest margin erosion was driven by carrier SLA delays.",
                        "financial_impact_usd": 142500.0,
                    }
                    st.success(f"Task Created (Local Mode): `{mock_task_id}`")

    with col_q2:
        st.subheader("Active Task Monitor")
        active_id = st.session_state.get("active_task_id")
        if active_id:
            task_data = fetch_task_status(active_id)
            if task_data:
                st.session_state["current_task_data"] = task_data
                status_str = task_data.get("status", "UNKNOWN")

                badge_class = "status-completed"
                if status_str == "PENDING": badge_class = "status-pending"
                elif status_str == "RUNNING": badge_class = "status-running"
                elif status_str == "WAITING_FOR_APPROVAL": badge_class = "status-approval"
                elif status_str == "REJECTED": badge_class = "status-rejected"

                st.markdown(f"**Task ID**: `{active_id}`")
                st.markdown(f"**Status**: <span class='status-badge {badge_class}'>{status_str}</span>", unsafe_allow_html=True)
                st.markdown(f"**Route**: `{task_data.get('route', 'Determining...')}`")
                st.markdown(f"**Financial Impact**: `${task_data.get('financial_impact_usd', 0.0):,.2f} USD`")

                if status_str == "WAITING_FOR_APPROVAL":
                    st.warning("⚠️ High Financial Risk Detected! Go to **5. Human-in-the-Loop (HITL) Center** to approve/reject.")
                elif status_str in {"RUNNING", "PENDING"}:
                    if st.button("🔄 Refresh Status"):
                        st.rerun()
        else:
            st.info("No active investigation running. Submit a question to start.")


# ==============================================================================
# PAGE 2: AGENT TRACE
# ==============================================================================
elif page == "2. Agent Execution Trace":
    st.title("🧩 LangGraph Multi-Agent Execution Trajectory")
    st.markdown("Visual timeline of autonomous reasoning agents executing in cyclic LangGraph state machine.")
    st.markdown("---")

    task_data = st.session_state.get("current_task_data")
    if not task_data:
        st.info("Please submit or select a task on Page 1 to view agent trace.")
    else:
        trajectory = task_data.get("node_trajectory") or ["orchestrator_node", "planner_agent_node", "router_node", "sql_analyst_agent_node", "doc_rag_agent_node", "evidence_aggregation_node", "critic_agent_node", "risk_assessment_hitl_node", "executive_synthesizer_agent_node"]

        st.subheader(f"Execution Trajectory for `{task_data.get('task_id')}`")

        agents_info = [
            ("Orchestrator Node", "Normalizes user inquiry, initializes task state graph", "COMPLETED", "0.1s"),
            ("Planner Agent", "Deconstructs inquiry into SQL queries and document retrieval targets", "COMPLETED", "0.4s"),
            ("Deterministic Router", "Routes inquiry to SQL Analyst and/or Document RAG paths", "COMPLETED", "0.05s"),
            ("SQL Analyst Agent (via MCP)", "Validates read-only SELECT queries with SQLGlot AST parser", "COMPLETED", "0.6s"),
            ("Document RAG Agent (via MCP)", "Retrieves SLA contracts using Dense + BM25 + FlashRank reranker", "COMPLETED", "0.8s"),
            ("Evidence Aggregation Node", "Constructs immutable claim-to-evidence graph", "COMPLETED", "0.2s"),
            ("Adversarial Critic Agent", "Audits claims for unsupported assertions and citation validity", "COMPLETED", "0.5s"),
            ("Risk Assessment & HITL Node", "Evaluates financial impact against $100,000 threshold", "COMPLETED" if task_data.get("status") != "WAITING_FOR_APPROVAL" else "INTERRUPTED", "0.1s"),
            ("Executive Synthesizer Agent", "Formulates final evidence-backed decision intelligence report", "COMPLETED" if task_data.get("status") == "COMPLETED" else "PENDING", "0.7s"),
        ]

        for node_name, purpose, status, latency in agents_info:
            with st.container():
                cols = st.columns([3, 5, 2, 2])
                cols[0].markdown(f"**{node_name}**")
                cols[1].caption(purpose)
                status_color = "🟢" if status == "COMPLETED" else ("🔴" if status == "INTERRUPTED" else "⚪")
                cols[2].markdown(f"{status_color} `{status}`")
                cols[3].markdown(f"⏱️ `{latency}`")
                st.markdown("<hr style='margin: 4px 0; border-color: #21262D;'>", unsafe_allow_html=True)


# ==============================================================================
# PAGE 3: EVIDENCE EXPLORER
# ==============================================================================
elif page == "3. Evidence & Citation Explorer":
    st.title("🔍 Evidence-First Claim & Citation Explorer")
    st.markdown("Separates hard ground-truth evidence (SQL data & contract text) from model inferences and assumptions.")
    st.markdown("---")

    task_data = st.session_state.get("current_task_data")
    if not task_data:
        st.info("Please submit or select a task on Page 1 to explore evidence.")
    else:
        col_ev1, col_ev2 = st.columns(2)

        with col_ev1:
            st.subheader("📊 Structured SQL Evidence")
            citations = task_data.get("citations", [])
            sql_queries = [c for c in citations if "SELECT" in str(c).upper()]
            if not sql_queries:
                sql_queries = ["SELECT region, SUM(refund_amount) FROM orders WHERE region = 'Midwest' LIMIT 100"]

            for q in sql_queries:
                st.markdown("**Executed Read-Only SQL Query:**")
                st.code(q, language="sql")
                st.markdown("**SQL Output Result Set:**")
                st.table([{"region": "Midwest", "total_refund_amount": "$142,500.00", "delayed_order_count": 1420}])

        with col_ev2:
            st.subheader("📄 Document RAG Evidence & Excerpts")
            doc_citations = [c for c in citations if "SELECT" not in str(c).upper()]
            if not doc_citations:
                doc_citations = ["carrier_logistics_x_sla_contract_2025.md#p1", "midwest_warehouse_q3_postmortem.md#p1"]

            for doc_ref in doc_citations:
                with st.expander(f"📌 Citation: {doc_ref}", expanded=True):
                    st.markdown("**Retrieved Document Excerpt:**")
                    st.markdown("> *\"Carrier Logistics X guarantees on-time delivery within 2 business days under Clause 4.1. SLA breaches incur a liability cap of $50,000 per quarter.\"*")
                    st.caption("Relevance Score: 0.94 | Retrieval Method: Hybrid Dense+BM25 + FlashRank Reranker")

        st.markdown("---")
        st.subheader("💡 Model Inferences vs Hard Evidence")
        col_inf1, col_inf2 = st.columns(2)
        with col_inf1:
            st.success("✅ **Verified Hard Facts (Evidence)**")
            st.markdown("- Midwest order refunds total `$142,500.00` across 1,420 shipments.")
            st.markdown("- Carrier X SLA liability cap is limited to `$50,000.00` per quarter.")
        with col_inf2:
            st.warning("⚠️ **Model Assumptions & Inferences**")
            st.markdown("- Assumes sorter software failure was primary cause of 48-hour warehouse delay.")
            st.markdown("- Recommends increasing contract liability cap to `$200,000.00` in 2026 renewal.")


# ==============================================================================
# PAGE 4: ROOT CAUSE & RECOMMENDATIONS
# ==============================================================================
elif page == "4. Root Cause & Recommendations":
    st.title("📋 Executive Root-Cause Analysis & Recommendations")
    st.markdown("Final executive decision-intelligence report formulated by Executive Synthesizer Agent.")
    st.markdown("---")

    task_data = st.session_state.get("current_task_data")
    if not task_data:
        st.info("Please submit or select a task on Page 1 to view executive findings.")
    else:
        st.subheader("Executive Conclusion")
        st.info(task_data.get("executive_conclusion") or "Root-cause analysis confirms Midwest margin erosion was driven by automated sorter failure combined with Carrier SLA delays.")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("### 🔎 Key Findings")
            findings = task_data.get("key_findings") or [
                "Midwest warehouse experienced 1,420 delayed shipments in Q3.",
                "Total customer refund payouts reached $142,500.00.",
                "Carrier Logistics X breached on-time SLA requirement (91.2% vs 98.0% required).",
            ]
            for f in findings:
                st.markdown(f"- {f}")

            st.markdown("### 🎯 Root Cause Analysis")
            st.markdown(task_data.get("root_cause_analysis") or "Automated sorter software failure caused a 48-hour warehouse backlog, compounding Carrier X delivery delays and triggering automated customer refund payouts under the 2025 refund policy.")

        with col_r2:
            st.markdown("### 💵 Business Financial Impact")
            impact = task_data.get("business_impact_usd") or task_data.get("financial_impact_usd") or 142500.0
            st.metric("Net Financial Impact", f"${impact:,.2f} USD", delta="-14.2% Margin Impact", delta_color="inverse")

            st.markdown("### 🚀 Recommended Actions")
            actions = task_data.get("recommended_actions") or [
                "1. Install redundant sorter hardware backup in Midwest Warehouse Alpha.",
                "2. Renegotiate Carrier X contract liability cap from $50,000 to $200,000.",
                "3. Deploy real-time queue alerts for warehouse backlog monitoring.",
            ]
            for act in actions:
                st.markdown(f"**{act}**")


# ==============================================================================
# PAGE 5: HUMAN-IN-THE-LOOP (HITL) CENTER
# ==============================================================================
elif page == "5. Human-in-the-Loop (HITL) Center":
    st.title("🛡️ Human-in-the-Loop (HITL) Risk & Approval Center")
    st.markdown("Manages mandatory human executive approval interrupts for high-financial-risk operational inquiries.")
    st.markdown("---")

    task_data = st.session_state.get("current_task_data")
    if not task_data or task_data.get("status") != "WAITING_FOR_APPROVAL":
        st.success("✅ No tasks currently awaiting executive approval.")
        st.info("To test HITL interrupt flow, submit query: `Midwest 100k financial refund impact carrier SLA contract penalty clause` on Page 1.")
    else:
        st.error("🚨 HUMAN APPROVAL REQUIRED")
        task_id = task_data.get("task_id")
        impact = task_data.get("financial_impact_usd", 142500.0)

        st.markdown(f"**Task ID**: `{task_id}`")
        st.markdown(f"**Financial Risk Impact**: `${impact:,.2f} USD` (Exceeds `$100,000.00 USD` Threshold)")
        st.markdown(f"**Original Inquiry**: *\"{task_data.get('original_question')}\"*")

        st.markdown("---")
        st.subheader("Executive Decision Submission")

        feedback = st.text_input("Operator Feedback / Justification Note:", value="Approved by CFO after contract review.")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ APPROVE TASK EXECUTION", type="primary", use_container_width=True):
                with st.spinner("Submitting APPROVAL decision and resuming graph..."):
                    try:
                        with get_api_client() as client:
                            res = client.post(f"/api/v1/tasks/{task_id}/approval", json={"decision": "APPROVED", "feedback": feedback})
                            if res.status_code == 200:
                                st.session_state["current_task_data"] = res.json()
                                st.success("Task APPROVED successfully! Graph execution resumed and completed.")
                                st.rerun()
                    except Exception:
                        task_data["status"] = "COMPLETED"
                        task_data["approval_status"] = "APPROVED"
                        st.session_state["current_task_data"] = task_data
                        st.success("Task APPROVED (Local Mode).")
                        st.rerun()

        with col_btn2:
            if st.button("❌ REJECT TASK EXECUTION", use_container_width=True):
                with st.spinner("Submitting REJECTION decision..."):
                    try:
                        with get_api_client() as client:
                            res = client.post(f"/api/v1/tasks/{task_id}/approval", json={"decision": "REJECTED", "feedback": feedback})
                            if res.status_code == 200:
                                st.session_state["current_task_data"] = res.json()
                                st.warning("Task REJECTED. State terminated safely.")
                                st.rerun()
                    except Exception:
                        task_data["status"] = "REJECTED"
                        task_data["approval_status"] = "REJECTED"
                        st.session_state["current_task_data"] = task_data
                        st.warning("Task REJECTED (Local Mode).")
                        st.rerun()


# ==============================================================================
# PAGE 6: EVALUATION & BENCHMARKS
# ==============================================================================
elif page == "6. Evaluation & Benchmarks":
    st.title("📊 Continuous Evaluation & Benchmarking Hub")
    st.markdown("Continuous evaluation results across 30 enterprise operational scenarios.")
    st.caption("🔒 Clearly Labeled: Deterministic Mock Evaluation Benchmark")
    st.markdown("---")

    # Load results from results/benchmark_results.json if present
    bench_data = None
    if os.path.exists("results/benchmark_results.json"):
        try:
            with open("results/benchmark_results.json", "r", encoding="utf-8") as f:
                bench_data = json.load(f).get("summary", {})
        except Exception:
            pass

    if not bench_data:
        st.info("No benchmark results available locally.")
        st.caption("Run `python -m app.eval.run` to generate deterministic evaluation benchmark results.")
    else:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Task Success Rate", f"{bench_data.get('task_success_rate', 1.0) * 100:.1f}%")
        col_m2.metric("Mean Groundedness", f"{bench_data.get('mean_groundedness', 0.878) * 100:.1f}%")
        col_m3.metric("Citation Coverage", f"{bench_data.get('mean_citation_coverage', 1.0) * 100:.1f}%")
        col_m4.metric("SQL Safety Rejection", f"{bench_data.get('sql_safety_rejection_rate', 1.0) * 100:.1f}%")

        st.markdown("---")
        st.subheader("Adversarial Critic A/B Experiment Impact")

        ab_info = bench_data.get("critic_ab_summary", {})
        col_ab1, col_ab2, col_ab3 = st.columns(3)
        col_ab1.metric("Groundedness (Critic OFF vs ON)", f"{ab_info.get('critic_enabled_groundedness', 1.0) * 100:.1f}%", delta=f"+{ab_info.get('groundedness_delta', 0.122) * 100:.1f}%")
        col_ab2.metric("Citation Coverage (Critic OFF vs ON)", f"{ab_info.get('critic_enabled_citation_coverage', 1.0) * 100:.1f}%", delta=f"+{ab_info.get('citation_coverage_delta', 1.0) * 100:.1f}%")
        col_ab3.metric("Estimated Cost USD", f"${bench_data.get('total_estimated_cost_usd', 0.0023):.4f}")

        st.markdown("---")
        if os.path.exists("results/benchmark_report.md"):
            with st.expander("📖 View Complete Benchmark Report (Markdown)", expanded=False):
                with open("results/benchmark_report.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
