import streamlit as st
import json
import plotly.graph_objects as go

from idix_engine import (
    calculate_idix_scores,
    determine_archetype,
    apply_scenario_adjustments
)

# ============================================================
# Load CSS
# ============================================================

def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# Load JSON Files
# ============================================================

def load_questions():
    with open("data/questions.json", "r") as f:
        return json.load(f)

def load_archetypes():
    with open("data/archetypes.json", "r") as f:
        return json.load(f)

def load_scenarios():
    with open("data/scenarios.json", "r") as f:
        return json.load(f)

questions_data = load_questions()
archetypes_data = load_archetypes()
scenarios_data = load_scenarios()

# ============================================================
# PAGE HEADER
# ============================================================

st.markdown("""
<div class='itype-container'>
    <h1>I-TYPE — Innovator Type Assessment</h1>
    <p class='subtitle'>Powered by IDIX — Innovator DNA Index™</p>
</div>
""", unsafe_allow_html=True)

st.write("")

# Tabs
tab1, tab2 = st.tabs(["Assessment", "Scenario Upgrade (Optional)"])

# ============================================================
# TAB 1 — QUESTIONNAIRE
# ============================================================

with tab1:

    answers = {}

    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)
    st.write("")

    for i, q in enumerate(questions_data):
        st.markdown(f"""
            <div class='itype-question-card'>
                <h3>{q['question']}</h3>
            </div>
        """, unsafe_allow_html=True)

        answer = st.slider("", 1, 5, 3, key=f"q_{i}")
        answers[q["question"]] = {
            "value": answer,
            "dimension": q["dimension"],
            "reverse": q["reverse"]
        }

    submitted = st.button("Submit Assessment", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# TAB 2 — SCENARIO REFINEMENT
# ============================================================

with tab2:

    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Scenario Upgrade (Optional)</h2>", unsafe_allow_html=True)
    st.write("These scenarios refine your Innovator DNA with real-world behaviour.")

    scenario_answers = {}

    for s in scenarios_data:
        st.markdown(f"""
        <div class='itype-question-card'>
            <h3>{s['scenario']}</h3>
        </div>
        """, unsafe_allow_html=True)

        choice = st.radio("", list(s["options"].keys()), key=s["id"])
        scenario_answers[s["id"]] = s["options"][choice]

    scenario_submit = st.button("Apply Scenario Refinement", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# RESULTS
# ============================================================

if submitted:

    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)

    # Base scoring
    scores = calculate_idix_scores(answers)

    # Apply scenario adjustments if chosen
    if scenario_submit:
        scores = apply_scenario_adjustments(scores, scenario_answers)

    # Determine archetype
    archetype_name, archetype_data = determine_archetype(scores, archetypes_data)

    st.markdown(f"""
        <div class='itype-result-card'>
            <h1 class='itype-result-title'>{archetype_name}</h1>
            <p style='text-align:center; opacity:0.85;'>{archetype_data['description']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Radar Chart
    dims = list(scores.keys())
    vals = list(scores.values())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=dims + [dims[0]],
        fill='toself',
        line_color='#00eaff'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(10,14,25,0.55)",
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e5f4ff')
    )

    st.markdown("<div class='itype-radar-container'>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Strengths & Risks
    st.markdown("<h3 style='margin-top:25px;'>Strengths & Growth Areas</h3>", unsafe_allow_html=True)
    st.markdown("<div class='itype-result-grid'>", unsafe_allow_html=True)

    for s in archetype_data["strengths"]:
        st.markdown(f"<div class='itype-strength-card'><strong>• {s}</strong></div>", unsafe_allow_html=True)

    for r in archetype_data["risks"]:
        st.markdown(f"<div class='itype-risk-card'><strong>• {r}</strong></div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)
