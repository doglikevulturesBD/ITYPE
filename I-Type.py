import streamlit as st
import json
import pandas as pd
from idix_engine import calculate_idix_scores, determine_archetype
import plotly.graph_objects as go
import base64

# ============================================================
# Load CSS
# ============================================================

def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# Load Questions + Archetypes
# ============================================================

def load_questions():
    with open("data/questions.json", "r") as f:
        return json.load(f)

def load_archetypes():
    with open("data/archetypes.json", "r") as f:
        return json.load(f)

questions_data = load_questions()
archetypes_data = load_archetypes()

# ============================================================
# PAGE HEADER
# ============================================================

st.markdown("""
<div class='itype-container'>
    <h1>I-TYPE — Innovator Type Assessment</h1>
    <p class='subtitle'>Powered by IDIX — Innovator DNA Index™</p>
</div>
""", unsafe_allow_html=True)

st.write("")  # spacing

# ============================================================
# TABS
# ============================================================

tab1, tab2 = st.tabs(["Assessment", "Scenario Upgrade (Optional)"])


# ============================================================
# QUIZ UI
# ============================================================

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

    answer = st.slider(
        label="",
        min_value=1, max_value=5, value=3, key=f"q{i}"
    )
    answers[q["question"]] = {
        "value": answer,
        "dimension": q["dimension"],
        "reverse": q["reverse"]
    }

st.write("")
submitted = st.button("Submit Assessment", key="submit", help="Calculate your Innovator Type now", 
                      use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)  # close questionnaire container

# ============================================================
# RESULTS
# ============================================================

if submitted:
    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)

    # ---- Calculate dimension scores ----
    scores = calculate_idix_scores(answers)

    # ---- Determine Archetype ----
    archetype_name, archetype_data = determine_archetype(scores, archetypes_data)

    # ---- Archetype Header ----
    st.markdown(f"""
        <div class='itype-result-card'>
            <h1 class='itype-result-title'>{archetype_name}</h1>
            <p style='text-align:center; opacity:0.85;'>
                {archetype_data['description']}
            </p>
        """, unsafe_allow_html=True)

    # ============================================================
    # RADAR CHART
    # ============================================================

    dimensions = list(scores.keys())
    values = list(scores.values())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=dimensions + [dimensions[0]],
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

    # ============================================================
    # STRENGTHS & RISKS
    # ============================================================

    st.markdown("<h3 style='margin-top:25px;'>Strengths & Growth Areas</h3>", unsafe_allow_html=True)
    st.markdown("<div class='itype-result-grid'>", unsafe_allow_html=True)

    for s in archetype_data["strengths"]:
        st.markdown(f"""
        <div class='itype-strength-card'>
            <strong>• {s}</strong>
        </div>
        """, unsafe_allow_html=True)

    for r in archetype_data["risks"]:
        st.markdown(f"""
        <div class='itype-risk-card'>
            <strong>• {r}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)  # close strengths grid + card


