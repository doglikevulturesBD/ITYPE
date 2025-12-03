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
# SESSION STATE SETUP (WIZARD FLOW)
# ============================================================

if "step" not in st.session_state:
    st.session_state.step = 1  # 1 = questions, 2 = scenarios, 3 = results

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "scenario_answers" not in st.session_state:
    st.session_state.scenario_answers = {}

if "use_scenarios" not in st.session_state:
    st.session_state.use_scenarios = False

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

# ============================================================
# SIMPLE STEP INDICATOR
# ============================================================

step_labels = {
    1: "Step 1 of 3 — Questionnaire",
    2: "Step 2 of 3 — Scenario Upgrade (Optional)",
    3: "Step 3 of 3 — Your Innovator Profile"
}

st.markdown(f"""
<div class='itype-container'>
<p style='text-align:center; opacity:0.85;'>{step_labels[st.session_state.step]}</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# STEP 1 — MAIN QUESTIONNAIRE
# ============================================================

if st.session_state.step == 1:
    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)
    st.write("Use the sliders to indicate how strongly each statement applies to you.")

    # Render all questions
    for i, q in enumerate(questions_data):
        st.markdown(f"""
            <div class='itype-question-card'>
            <h3>{q['question']}</h3>
            </div>
        """, unsafe_allow_html=True)

        # Use Streamlit state-backed sliders
        val = st.slider(
            label="",
            min_value=1,
            max_value=5,
            value=3,
            key=f"q_{i}"
        )

    # Button to go to Step 2
    if st.button("Next: Scenario Upgrade (Optional)", use_container_width=True):
        # Build answers dict from slider values
        answers = {}
        for i, q in enumerate(questions_data):
            slider_value = st.session_state.get(f"q_{i}", 3)
            answers[q["question"]] = {
                "value": slider_value,
                "dimension": q["dimension"],
                "reverse": q["reverse"]
            }
        st.session_state.answers = answers
        st.session_state.step = 2

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# STEP 2 — SCENARIO MODULE (OPTIONAL)
# ============================================================

elif st.session_state.step == 2:
    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Scenario Upgrade (Optional)</h2>", unsafe_allow_html=True)
    st.write("These 10 short scenarios refine your profile based on real-world behaviour. You can skip this step if you prefer.")

    # Render all scenarios
    for s in scenarios_data:
        st.markdown(f"""
        <div class='itype-question-card'>
        <h3>{s['scenario']}</h3>
        </div>
        """, unsafe_allow_html=True)

        choice = st.radio(
            label="Select your response:",
            options=list(s["options"].keys()),
            key=s["id"]
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Skip Scenarios & View My Profile", use_container_width=True):
            st.session_state.use_scenarios = False
            st.session_state.scenario_answers = {}
            st.session_state.step = 3

    with col2:
        if st.button("Use Scenarios to Refine My Profile", use_container_width=True):
            scenario_answers = {}
            for s in scenarios_data:
                selected = st.session_state.get(s["id"])
                if selected:
                    scenario_answers[s["id"]] = s["options"][selected]
            st.session_state.scenario_answers = scenario_answers
            st.session_state.use_scenarios = True
            st.session_state.step = 3

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# STEP 3 — RESULTS
# ============================================================

elif st.session_state.step == 3:
    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)

    if not st.session_state.answers:
        st.warning("Please complete the questionnaire first.")
        if st.button("Go to Step 1"):
            st.session_state.step = 1
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Base scoring from questionnaire
        scores = calculate_idix_scores(st.session_state.answers)

        # Optional scenario refinement
        if st.session_state.use_scenarios and st.session_state.scenario_answers:
            scores = apply_scenario_adjustments(scores, st.session_state.scenario_answers)

        # Determine Archetype
        archetype_name, archetype_data = determine_archetype(scores, archetypes_data)

        # Header
        st.markdown(f"""
            <div class='itype-result-card'>
            <h1 class='itype-result-title'>{archetype_name}</h1>
            <p style='text-align:center; opacity:0.85;'>
                {archetype_data['description']}
            </p>
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

        for s in archetype_data.get("strengths", []):
            st.markdown(f"""
            <div class='itype-strength-card'>
            <strong>• {s}</strong>
            </div>
            """, unsafe_allow_html=True)

        for r in archetype_data.get("risks", []):
            st.markdown(f"""
            <div class='itype-risk-card'>
            <strong>• {r}</strong>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Optional extra info (if using extended archetypes.json)
        if "trl_affinity" in archetype_data or "pathway_suggestions" in archetype_data:
            st.markdown("<h3 style='margin-top:25px;'>Innovation Context</h3>", unsafe_allow_html=True)
            if "trl_affinity" in archetype_data:
                st.markdown(f"""
                <div class='itype-context-card'>
                    <strong>TRL Affinity:</strong><br>{archetype_data['trl_affinity']}
                </div>
                """, unsafe_allow_html=True)

            if "pathway_suggestions" in archetype_data:
                st.markdown("<div class='itype-context-card'><strong>Suggested Pathways:</strong><br>", unsafe_allow_html=True)
                for p in archetype_data["pathway_suggestions"]:
                    st.markdown(f"• {p}")
                st.markdown("</div>", unsafe_allow_html=True)

        # Reset / Restart Options
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Back to Scenarios", use_container_width=True):
                st.session_state.step = 2

        with col_b:
            if st.button("Restart Assessment", use_container_width=True):
                st.session_state.step = 1
                st.session_state.answers = {}
                st.session_state.scenario_answers = {}
                st.session_state.use_scenarios = False
                # sliders/radios will reset naturally on reload

        st.markdown("</div>", unsafe_allow_html=True)
