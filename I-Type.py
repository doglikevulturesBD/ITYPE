import streamlit as st
import json
from idix_engine import compute_idix

# ============================================================
# CSS LOADING
# ============================================================

def load_css():
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_css()

# ============================================================
# LOAD DATA
# ============================================================

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

questions_data = load_json("data/questions.json")
archetypes_data = load_json("data/archetypes.json")
scenarios_data = load_json("data/scenarios.json")

# ============================================================
# PAGE HEADER
# ============================================================

st.markdown("""
<div class='itype-container'>
    <h1>I-TYPE — Innovator Type Assessment</h1>
    <p class='subtitle'>Powered by <strong>IDIX — Innovator DNA Index™</strong></p>
</div>
""", unsafe_allow_html=True)

st.write("")

# ============================================================
# QUESTIONNAIRE
# ============================================================

st.markdown("<h2 style='text-align:center;'>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)
st.write("")

answers = {}

for i, q in enumerate(questions_data):

    # question card
    st.markdown(f"""
        <div class='itype-question-card'>
            <h3>{q['question']}</h3>
        </div>
    """, unsafe_allow_html=True)

    # slider description tooltip
    low_label = q.get("low_label", "Low")
    high_label = q.get("high_label", "High")

    with st.container():
        c1, c2 = st.columns([0.2, 0.8])
        with c1:
            st.markdown(f"<p style='opacity:0.6; font-size:0.85rem'>{low_label}</p>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<p style='text-align:right; opacity:0.6; font-size:0.85rem'>{high_label}</p>", unsafe_allow_html=True)

    answer = st.slider(
        label="",
        min_value=1,
        max_value=5,
        value=3,
        key=f"q{i}",
        help=f"{low_label} ← slider → {high_label}",
    )

    answers[q["question"]] = {
        "value": answer,
        "dimension": q["dimension"],
        "reverse": q.get("reverse", False)
    }

st.write("")
submitted = st.button("Submit Assessment", use_container_width=True)

# ============================================================
# RESULTS
# ============================================================

if submitted:
    st.markdown("<div class='itype-container'>", unsafe_allow_html=True)

    # Compute IDIX results
    final_scores, (primary_name, primary_data), (shadow_name, shadow_data) = compute_idix(
        answers,
        scenario_responses=None,
        scenario_weights=None,
        archetypes=archetypes_data
    )

    # ------------------------------
    # PRIMARY ARCHETYPE CARD
    # ------------------------------

    st.markdown(f"""
        <div class='itype-result-card'>
            <h1 class='itype-result-title'>{primary_name}</h1>
            <p style='text-align:center; opacity:0.85;'>{primary_data["description"]}</p>
    """, unsafe_allow_html=True)

    # ------------------------------
    # SHADOW ARCHETYPE
    # ------------------------------

    st.markdown("""
        <hr style='margin:25px 0; opacity:0.25;'>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <h3 style='text-align:center;'>Shadow Archetype: {shadow_name}</h3>
        <p style='text-align:center; opacity:0.65;'>
            {shadow_data.get("description", "A secondary innovation tendency that shapes your approach.")}
        </p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # STRENGTHS & RISKS GRID
    # ============================================================

    st.markdown("<h3 style='margin-top:25px;'>Strengths & Growth Areas</h3>", unsafe_allow_html=True)
    st.markdown("<div class='itype-result-grid'>", unsafe_allow_html=True)

    # Strengths
    for s in primary_data.get("strengths", []):
        st.markdown(f"""
        <div class='itype-strength-card'>
            <strong>• {s}</strong>
        </div>
        """, unsafe_allow_html=True)

    # Risks
    for r in primary_data.get("risks", []):
        st.markdown(f"""
        <div class='itype-risk-card'>
            <strong>• {r}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # SCORE BREAKDOWN
    # ============================================================

    st.markdown("<h3 style='margin-top:35px;'>Your Innovation DNA (Score Breakdown)</h3>", unsafe_allow_html=True)

    score_table = {dim: round(val, 1) for dim, val in final_scores.items()}
    st.table(score_table)

    st.markdown("</div>", unsafe_allow_html=True)
