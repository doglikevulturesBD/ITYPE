import streamlit as st
import json
import plotly.graph_objects as go

from idix_engine import (
    normalize_scores,
    combine_with_scenarios,
    determine_archetype,
    monte_carlo_probabilities
)

# ============================================================
# LOAD CSS
# ============================================================

def load_css():
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        st.warning("⚠ CSS file missing (assets/styles.css)")

load_css()

# ============================================================
# SAFE JSON LOADING
# ============================================================

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return []

questions = load_json("data/questions.json")
archetypes = load_json("data/archetypes.json")
scenarios = load_json("data/scenarios.json")

# ============================================================
# PAGE HEADER
# ============================================================

st.markdown("""
<div class='itype-container'>
<h1>I-TYPE — Innovator Type Assessment</h1>
<p class='subtitle'>Powered by the Innovator DNA Index™</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔍 Assessment", "🧪 Scenarios", "📊 Results"])

# ============================================================
# TAB 1 — QUESTIONS
# ============================================================

with tabs[0]:

    st.markdown("<h2>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)
    answers = {}

    if not questions:
        st.error("❌ No questions loaded. Check data/questions.json")
    else:
        for i, q in enumerate(questions):

            text = q.get("question", f"Question {i+1}")
            dim = q.get("dimension", "unknown")
            reverse = q.get("reverse", False)

            st.markdown(f"""
            <div class='itype-question-card'>
            <h3>{text}</h3>
            </div>
            """, unsafe_allow_html=True)

            low_label = q.get("labels", {}).get("low", "Low")
            high_label = q.get("labels", {}).get("high", "High")

            answers[text] = {
                "value": st.slider(
                    label="",
                    min_value=1, max_value=5, value=3,
                    help=f"1 = {low_label}   •   5 = {high_label}",
                    key=f"q{i}"
                ),
                "dimension": dim,
                "reverse": reverse
            }

# ============================================================
# TAB 2 — SCENARIOS
# ============================================================

with tabs[1]:

    st.markdown("<h2>Scenario-Based Assessment</h2>", unsafe_allow_html=True)

    scenario_scores_raw = {k: 0 for k in ["thinking", "execution", "risk", "motivation", "team", "commercial"]}
    count = 0

    if not scenarios:
        st.error("❌ No scenarios loaded. Check data/scenarios.json")

    else:
        for i, sc in enumerate(scenarios):

            title = sc.get("title", f"Scenario {i+1}")
            desc = sc.get("description", "No description provided.")

            st.markdown(f"""
            <div class='itype-scenario-card'>
            <h3>{title}</h3>
            <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

            options = sc.get("options", ["Option A", "Option B"])
            mapping = sc.get("mapping", {})

            choice = st.selectbox("Choose your response:", options, key=f"sc{i}")

            score_vec = mapping.get(choice, {
                "thinking": 0, "execution": 0, "risk": 0,
                "motivation": 0, "team": 0, "commercial": 0
            })

            for k in scenario_scores_raw:
                scenario_scores_raw[k] += score_vec.get(k, 0)

            count += 1

        # SAFE NORMALIZATION
        if count > 0:
            scenario_scores = {k: scenario_scores_raw[k] / count for k in scenario_scores_raw}
        else:
            scenario_scores = scenario_scores_raw.copy()

# ============================================================
# TAB 3 — RESULTS
# ============================================================

with tabs[2]:

    st.markdown("<h2>Your Results</h2>", unsafe_allow_html=True)

    calculate = st.button("Calculate My Innovator Type")

    if calculate:

        # ——————————————————————————————
        # STEP 1: Normalise questionnaire
        # ——————————————————————————————
        q_scores = normalize_scores(answers)

        # ——————————————————————————————
        # STEP 2: Combine with scenarios
        # ——————————————————————————————
        final = combine_with_scenarios(q_scores, scenario_scores)

        # ——————————————————————————————
        # STEP 3: Archetype
        # ——————————————————————————————
        archetype_name, archetype_data = determine_archetype(final, archetypes)

        if archetype_name == "Undefined":
            st.warning("⚠ Your profile is evenly balanced — no single archetype dominates.")

        st.markdown(f"""
        <div class='itype-result-card'>
        <h1>{archetype_name}</h1>
        <p>{archetype_data.get("description", "No description available.")}</p>
        </div>
        """, unsafe_allow_html=True)

        # ——————————————————————————————
        # RADAR CHART
        # ——————————————————————————————
        dims = list(final.keys())
        vals = list(final.values())

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=dims + [dims[0]],
            fill='toself',
            line_color='#00eaff'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
                bgcolor='rgba(10,14,25,0.55)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5f4ff'),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # ——————————————————————————————
        # MONTE CARLO SIMULATION
        # ——————————————————————————————
        probs, stability, shadow = monte_carlo_probabilities(final, archetypes)

        st.markdown("<h3>Monte-Carlo Stability Analysis</h3>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='itype-stability-card'>
        <h2>Stability Score: {stability:.1f}%</h2>
        <p>Stability = how consistently your archetype appears across 5000 simulated variations.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### Shadow Archetype: **{shadow[0]}** ({shadow[1]:.1f}%)")

        # BAR CHART
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=list(probs.keys()),
            y=list(probs.values()),
            marker_color="#00eaff"
        ))
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5f4ff'),
            yaxis_title="Probability (%)"
        )

        st.plotly_chart(fig2, use_container_width=True)

        # ============================================================
        # DETAILED BREAKDOWN
        # ============================================================

        st.markdown("<hr><h2>Your Innovator Breakdown</h2>", unsafe_allow_html=True)

        # Strengths
        st.markdown("<h3>Strengths</h3>", unsafe_allow_html=True)
        for s in archetype_data.get("strengths", []):
            st.markdown(f"<div class='itype-strength-card'>• {s}</div>", unsafe_allow_html=True)

        # Risks
        st.markdown("<h3 style='margin-top:20px;'>Growth Edges & Risks</h3>", unsafe_allow_html=True)
        for r in archetype_data.get("risks", []):
            st.markdown(f"<div class='itype-risk-card'>• {r}</div>", unsafe_allow_html=True)

        # Pathways
        st.markdown("<h3 style='margin-top:20px;'>Recommended Innovation Pathways</h3>", unsafe_allow_html=True)
        for p in archetype_data.get("pathways", []):
            st.markdown(f"<div class='itype-pathway-card'>• {p}</div>", unsafe_allow_html=True)

        # Business Models
        st.markdown("<h3 style='margin-top:20px;'>Suggested Business Models</h3>", unsafe_allow_html=True)
        for bm in archetype_data.get("business_models", []):
            st.markdown(f"<div class='itype-business-card'>• {bm}</div>", unsafe_allow_html=True)

        # Funding Fit
        st.markdown("<h3 style='margin-top:20px;'>Funding Strategy Fit</h3>", unsafe_allow_html=True)
        for fs in archetype_data.get("funding_strategy", []):
            st.markdown(f"<div class='itype-funding-card'>• {fs}</div>", unsafe_allow_html=True)

    else:
        st.info("Click **Calculate My Innovator Type** to see results.")
