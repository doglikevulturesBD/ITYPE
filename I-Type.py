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
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# LOAD JSON FILES
# ============================================================

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

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

    for i, q in enumerate(questions):
        st.markdown(f"""
        <div class='itype-question-card'>
            <h3>{q["question"]}</h3>
        </div>
        """, unsafe_allow_html=True)

        key = f"q{i}"

        # SAFE: avoid KeyError if labels missing
        low_label = q.get("labels", {}).get("low", "Low")
        high_label = q.get("labels", {}).get("high", "High")

        answers[q["question"]] = {
            "value": st.slider(
                label="",
                min_value=1, max_value=5, value=3,
                help=f"1 = {low_label}   •   5 = {high_label}",
                key=key
            ),
            "dimension": q["dimension"],
            "reverse": q["reverse"]
        }


# ============================================================
# TAB 2 — SCENARIOS
# ============================================================

with tabs[1]:
    st.markdown("<h2>Scenario-Based Assessment</h2>", unsafe_allow_html=True)

    scenario_scores_raw = {"thinking": 0, "execution": 0, "risk": 0, "motivation": 0, "team": 0, "commercial": 0}
    count = 0

    for i, sc in enumerate(scenarios):

        # SAFE: Avoid KeyError for missing title
        title = sc.get("title", f"Scenario {i+1}")
        desc = sc.get("description", "No description provided.")

        st.markdown(f"""
        <div class='itype-scenario-card'>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

        # SAFE: ensure options exist
        options = sc.get("options", ["Option A", "Option B"])
        mapping = sc.get("mapping", {})

        choice = st.selectbox(
            "Choose your response:",
            options,
            key=f"sc{i}"
        )

        # SAFE: if mapping missing, assume zero vector
        score_vec = mapping.get(choice, {
            "thinking": 0, "execution": 0, "risk": 0,
            "motivation": 0, "team": 0, "commercial": 0
        })

        for k in scenario_scores_raw:
            scenario_scores_raw[k] += score_vec[k]
        count += 1

    # Normalize scenario contributions
    if count > 0:
        scenario_scores = {k: (scenario_scores_raw[k] / count) for k in scenario_scores_raw}
    else:
        scenario_scores = scenario_scores_raw.copy()

# ============================================================
# TAB 3 — RESULTS
# ============================================================

with tabs[2]:
    if st.button("Calculate My Innovator Type"):
        st.markdown("<h2>Your Innovation Profile</h2>", unsafe_allow_html=True)

        # Step 1 — Questionnaire → scores
        q_scores = normalize_scores(answers)

        # Step 2 — Combine with scenarios
        final = combine_with_scenarios(q_scores, scenario_scores)

        # Step 3 — Archetype
        archetype_name, archetype_data = determine_archetype(final, archetypes)

        st.markdown(f"""
        <div class='itype-result-card'>
            <h1>{archetype_name}</h1>
            <p>{archetype_data["description"]}</p>
        </div>
        """, unsafe_allow_html=True)

        # Step 4 — Radar Chart
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

        # Step 5 — Monte Carlo Simulation
        probs, stability, shadow = monte_carlo_probabilities(final, archetypes)

        st.markdown("<h3>Monte-Carlo Stability Analysis</h3>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='itype-stability-card'>
            <h2>Stability Score: {stability:.1f}%</h2>
            <p>This indicates how consistently your archetype appears across 5000 simulated variations.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### Shadow Archetype: **{shadow[0]}** ({shadow[1]:.1f}%)")

        # Probability bars
        st.markdown("### Archetype Probabilities")

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

