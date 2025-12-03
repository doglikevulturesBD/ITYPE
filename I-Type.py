import streamlit as st
import json
import os
import plotly.graph_objects as go
from idix_engine import calculate_idix_scores, determine_archetype

# ============================================================
# PATHING (Bulletproof fix for JSONDecodeError)
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json(filename):
    path = os.path.join(BASE_DIR, "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load data
questions_data = load_json("questions.json")
archetypes_data = load_json("archetypes.json")
scenarios_data = load_json("scenarios.json")

# ============================================================
# Load CSS
# ============================================================
def load_css():
    path = os.path.join(BASE_DIR, "assets", "styles.css")
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# PAGE HEADER
# ============================================================
st.markdown("""
<div class='itype-container'>
<h1>I-TYPE — Innovator Type Assessment</h1>
<p class='subtitle'>Powered by the IDIX™ — Innovator DNA Index</p>
</div>
""", unsafe_allow_html=True)

st.write("")

# ============================================================
# TAB SETUP
# ============================================================
tab1, tab2, tab3 = st.tabs(["📘 Questionnaire", "🎭 Scenarios", "📊 Results"])

# ============================================================
# TAB 1 — QUESTIONNAIRE
# ============================================================
with tab1:
    st.markdown("<h2 class='itype-title'>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)

    q_answers = {}

    for i, q in enumerate(questions_data):

        # --- Card wrapper ---
        st.markdown(f"""
        <div class='itype-question-card'>
        <h3>{q['question']}</h3>
        </div>
        """, unsafe_allow_html=True)

        # --- Brand-colour slider labels ---
        cols = st.columns([1, 6, 1])

        with cols[0]:
            st.markdown(
                "<div style='text-align:center; color:#00eaff; opacity:0.85;'>"
                "1<br><small>Disagree</small></div>",
                unsafe_allow_html=True
            )

        with cols[1]:
            answer = st.slider(
                label="",
                min_value=1,
                max_value=5,
                value=3,
                key=f"q{i}",
                help="1 = Disagree · 5 = Agree"
            )

        with cols[2]:
            st.markdown(
            "<div style='text-align:center; color:#ff4bf1; opacity:0.85;'>"
            "5<br><small>Agree</small></div>",
                unsafe_allow_html=True
            )

        q_answers[q["id"]] = {
            "value": answer,
            "dimension": q["dimension"],
            "reverse": q["reverse"]
        }

# ============================================================
# TAB 2 — SCENARIOS
# ============================================================
with tab2:
    st.markdown("<h2 class='itype-title'>Scenario-Based Behaviour Assessment</h2>", unsafe_allow_html=True)

    scenario_answers = {}

    for s in scenarios_data:
        st.markdown(f"""
        <div class='itype-question-card'>
        <h3>{s['scenario']}</h3>
        </div>
        """, unsafe_allow_html=True)

        options = [opt["text"] for opt in s["options"]]

        choice = st.radio(
            label="Choose your response:",
            options=options,
            key=f"sc{s['id']}"
        )

        for opt in s["options"]:
            if opt["text"] == choice:
                scenario_answers[s["id"]] = opt["dimension"]

# ============================================================
# TAB 3 — RESULTS
# ============================================================
with tab3:
    st.markdown("<h2 class='itype-title'>Your Results</h2>", unsafe_allow_html=True)

    submitted = st.button("Calculate My Innovator Type", use_container_width=True)

    if submitted:

        # ==============================================
        # 1. CALCULATE BASE SCORES
        # ==============================================
        base_scores = calculate_idix_scores(q_answers)

        # ==============================================
        # 2. APPLY SCENARIO BOOST
        # ==============================================
        scenario_boost = 3
        scenario_scores = {dim: 0 for dim in base_scores}

        for sc_id, dim in scenario_answers.items():
            scenario_scores[dim] += scenario_boost

        final_scores = {
            dim: min(100, base_scores[dim] + scenario_scores[dim])
            for dim in base_scores
        }

        # ==============================================
        # 3. DETERMINE ARCHETYPE
        # ==============================================
        archetype_name, archetype_data = determine_archetype(final_scores, archetypes_data)

        # ============================================================
        # DISPLAY ARCHETYPE CARD
        # ============================================================
        st.markdown(f"""
        <div class='itype-result-card'>
        <h1 class='itype-result-title'>{archetype_name}</h1>
        <p style='text-align:center; opacity:0.85;'>{archetype_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)

        # ============================================================
        # RADAR CHART
        # ============================================================
        dims = list(final_scores.keys())
        vals = list(final_scores.values())

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
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5f4ff'),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # ============================================================
        # STRENGTHS + RISKS
        # ============================================================
        st.markdown("<h3>Strengths & Growth Areas</h3>", unsafe_allow_html=True)
        st.markdown("<div class='itype-result-grid'>", unsafe_allow_html=True)

        for s in archetype_data["strengths"]:
            st.markdown(f"<div class='itype-strength-card'>• {s}</div>", unsafe_allow_html=True)

        for r in archetype_data["risks"]:
            st.markdown(f"<div class='itype-risk-card'>• {r}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


        st.markdown("</div>", unsafe_allow_html=True)
