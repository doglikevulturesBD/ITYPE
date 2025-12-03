import streamlit as st
import json
import os
import plotly.graph_objects as go
from idix_engine import calculate_question_scores, determine_archetypes

# ============================================================
# PATHING & HELPERS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json(filename):
    path = os.path.join(BASE_DIR, "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_css():
    css_path = os.path.join(BASE_DIR, "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# LOAD DATA
# ============================================================

questions_data = load_json("questions.json")
archetypes_data = load_json("archetypes.json")
scenarios_data = load_json("scenarios.json")

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
# TABS
# ============================================================

tab_q, tab_s, tab_r = st.tabs(["📘 Questionnaire", "🎭 Scenarios", "📊 Results"])

# Use session_state to persist answers across tabs
if "answers" not in st.session_state:
    st.session_state["answers"] = {}
if "scenario_choices" not in st.session_state:
    st.session_state["scenario_choices"] = {}

# ============================================================
# TAB 1 — QUESTIONNAIRE
# ============================================================

with tab_q:
    st.markdown("<h2 class='itype-title'>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)
    st.write("")

    answers = st.session_state["answers"]

    for i, q in enumerate(questions_data):

        st.markdown(f"""
        <div class='itype-question-card'>
        <h3>{q['question']}</h3>
        </div>
        """, unsafe_allow_html=True)

        # Brand-colour slider labels (Disagree ↔ Agree)
        cols = st.columns([1, 6, 1])

        with cols[0]:
            st.markdown(
            "<div style='text-align:center; color:#00eaff; opacity:0.85;'>"
            "1<br><small>Disagree</small></div>",
                unsafe_allow_html=True
            )

        with cols[1]:
            val = st.slider(
                label="",
                min_value=1,
                max_value=5,
                value=answers.get(q["id"], {}).get("value", 3),
                key=f"q_{q['id']}",
                help="1 = Disagree · 5 = Agree"
            )

        with cols[2]:
            st.markdown(
            "<div style='text-align:center; color:#ff4bf1; opacity:0.85;'>"
            "5<br><small>Agree</small></div>",
                unsafe_allow_html=True
            )

        # Store full info in session_state
        answers[q["id"]] = {
            "value": val,
            "dimension": q["dimension"],
            "reverse": q.get("reverse", False)
        }

    st.session_state["answers"] = answers

# ============================================================
# TAB 2 — SCENARIOS
# ============================================================

with tab_s:
    st.markdown("<h2 class='itype-title'>Scenario-Based Behaviour</h2>", unsafe_allow_html=True)
    st.write("")

    scenario_choices = st.session_state["scenario_choices"]

    for s in scenarios_data:
        st.markdown(f"""
            <div class='itype-question-card'>
                <h3>{s['scenario']}</h3>
            </div>
        """, unsafe_allow_html=True)

        option_texts = [opt["text"] for opt in s["options"]]

        # Restore previous choice if exists
        prev_choice = scenario_choices.get(s["id"], None)

        choice = st.radio(
            label="How would you respond?",
            options=option_texts,
            index=option_texts.index(prev_choice) if prev_choice in option_texts else 0,
            key=f"sc_{s['id']}"
        )

        scenario_choices[s["id"]] = choice

    st.session_state["scenario_choices"] = scenario_choices

# ============================================================
# TAB 3 — RESULTS
# ============================================================

with tab_r:
    st.markdown("<h2 class='itype-title'>Your Innovator Profile</h2>", unsafe_allow_html=True)
    st.write("")

    submitted = st.button("Calculate My Innovator Type", use_container_width=True)

    if submitted:
        answers = st.session_state["answers"]
        scenario_choices = st.session_state["scenario_choices"]

        # --------------------------------------------
        # 1) QUESTION SCORES (0–100 per dimension)
        # --------------------------------------------
        base_scores = calculate_question_scores(answers)

        # --------------------------------------------
        # 2) SCENARIO PULL-IN (multi-choice)
        #    Each chosen option boosts its target dimension.
        # --------------------------------------------
        scenario_boost = 3  # tweakable knob
        scenario_scores = {dim: 0 for dim in base_scores}

        for s in scenarios_data:
            chosen_text = scenario_choices.get(s["id"], None)
            if not chosen_text:
                continue

            # Find the option's dimension
            for opt in s["options"]:
                if opt["text"] == chosen_text:
                    dim = opt["dimension"]
                    if dim in scenario_scores:
                        scenario_scores[dim] += scenario_boost
                    break

        final_scores = {
            dim: min(100, base_scores[dim] + scenario_scores.get(dim, 0))
            for dim in base_scores
        }

        # --------------------------------------------
        # 3) DETERMINE PRIMARY + SHADOW ARCHETYPES
        # --------------------------------------------
        (primary_name, primary_data), (shadow_name, shadow_data) = determine_archetypes(
            final_scores,
            archetypes_data
        )

        # --------------------------------------------
        # 4) DISPLAY ARCHETYPE CARD
        # --------------------------------------------
        st.markdown(f"""
        <div class='itype-result-card'>
        <h1 class='itype-result-title'>{primary_name}</h1>
        <p style='text-align:center; opacity:0.85;'>{primary_data["description"]}</p>

        <hr style='margin:20px 0; opacity:0.25;'>

        <h3 style='text-align:center;'>Shadow Archetype: {shadow_name}</h3>
        <p style='text-align:center; opacity:0.7;'>
                {shadow_data.get("description", "A secondary innovation tendency that shapes your approach.")}
        </p>
        </div>
        """, unsafe_allow_html=True)

        # --------------------------------------------
        # 5) RADAR CHART
        # --------------------------------------------
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

        # --------------------------------------------
        # 6) STRENGTHS & RISKS
        # --------------------------------------------
        st.markdown("<h3 style='margin-top:25px;'>Strengths & Growth Areas</h3>", unsafe_allow_html=True)
        st.markdown("<div class='itype-result-grid'>", unsafe_allow_html=True)

        for s in primary_data.get("strengths", []):
            st.markdown(f"<div class='itype-strength-card'>• {s}</div>", unsafe_allow_html=True)

        for r in primary_data.get("risks", []):
            st.markdown(f"<div class='itype-risk-card'>• {r}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # --------------------------------------------
        # 7) SCORE BREAKDOWN TABLE
        # --------------------------------------------
        st.markdown("<h3 style='margin-top:35px;'>Your Innovation DNA — Score Breakdown</h3>", unsafe_allow_html=True)
        score_table = {dim: round(val, 1) for dim, val in final_scores.items()}
        st.table(score_table)

        # --------------------------------------------
        # 8) RETAKE BUTTON
        # --------------------------------------------
        if st.button("Retake Assessment", use_container_width=True):
            st.session_state["answers"] = {}
            st.session_state["scenario_choices"] = {}
            st.experimental_rerun()

