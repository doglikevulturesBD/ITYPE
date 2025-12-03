import streamlit as st
import json
import plotly.graph_objects as go

from idix_engine import (
    normalize_scores,
    combine_with_scenarios,
    determine_archetype,
    monte_carlo_probabilities,
)

# ============================================================
# SESSION STATE INITIALISATION
# ============================================================

if "step" not in st.session_state:
    st.session_state["step"] = 1  # 1 = Questions, 2 = Scenarios, 3 = Results


# ============================================================
# LOAD CSS
# ============================================================

def load_css():
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠ Missing CSS file: assets/styles.css")

load_css()


# ============================================================
# LOAD JSON HELPERS
# ============================================================

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return default

questions = load_json("data/questions.json", default=[])
archetypes = load_json("data/archetypes.json", default={})
scenarios = load_json("data/scenarios.json", default=[])


# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div class="hero-wrapper">
  <div class="hero">
    <div class="hero-glow"></div>
    <div class="hero-particles"></div>
    <div class="hero-content">
      <h1 class="hero-title">I-TYPE — Innovator Type Assessment</h1>
      <p class="hero-sub">Powered by the Innovator DNA Index™</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# STEP PROGRESS BAR
# ============================================================

step = st.session_state["step"]
total_steps = 3

step_labels = {
    1: "Step 1 of 3 — Innovation Profile Questionnaire",
    2: "Step 2 of 3 — Scenario-Based Assessment",
    3: "Step 3 of 3 — Your Innovator Type & Results",
}

st.markdown(f"### {step_labels[step]}")
st.progress(step / total_steps)


# ============================================================
# HELPERS TO RECONSTRUCT ANSWERS & SCENARIOS FROM STATE
# ============================================================

def get_answers_from_state(questions_list):
    """
    Rebuilds the `answers` dict from stored slider values in session_state.
    """
    answers = {}
    for i, q in enumerate(questions_list):
        text = q.get("question", f"Question {i+1}")
        dim = q.get("dimension", "thinking")
        reverse = q.get("reverse", False)
        val = st.session_state.get(f"q{i}", 3)
        answers[text] = {
            "value": val,
            "dimension": dim,
            "reverse": reverse,
        }
    return answers


def get_scenario_scores_from_state(scenarios_list):
    """
    Uses stored selectbox choices to compute scenario_scores across dimensions.
    """
    accum = {
        "thinking": 0,
        "execution": 0,
        "risk": 0,
        "motivation": 0,
        "team": 0,
        "commercial": 0,
    }
    count = 0

    for i, sc in enumerate(scenarios_list):
        mapping = sc.get("mapping", {})
        options = sc.get("options", [])
        choice = st.session_state.get(f"sc_{i}")

        if choice is None or choice not in mapping:
            # If not answered or mapping missing, skip
            continue

        vec = mapping.get(choice, {})
        for k in accum:
            accum[k] += vec.get(k, 0)
        count += 1

    if count == 0:
        return accum.copy()

    return {k: accum[k] / count for k in accum}


# ============================================================
# STEP 1 — QUESTIONNAIRE
# ============================================================

if step == 1:

    if not questions:
        st.error("❌ No questions found. Check data/questions.json.")
    else:
        for i, q in enumerate(questions):
            text = q.get("question", f"Question {i+1}")
            dim = q.get("dimension", "thinking")
            reverse = q.get("reverse", False)

            st.markdown(f"""
            <div class='itype-question-card'>
                <h3>{text}</h3>
            </div>
            """, unsafe_allow_html=True)

            # Basic slider (labels handled in future if needed)
            st.slider(
                label="",
                min_value=1,
                max_value=5,
                value=st.session_state.get(f"q{i}", 3),
                key=f"q{i}"
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Reset"):
            for key in list(st.session_state.keys()):
                if key.startswith("q") or key.startswith("sc_"):
                    del st.session_state[key]
            st.session_state["step"] = 1
            st.rerun()

    with col2:
        if st.button("Next ➜ Scenarios"):
            st.session_state["step"] = 2
            st.rerun()


# ============================================================
# STEP 2 — SCENARIOS
# ============================================================

elif step == 2:

    if not scenarios:
        st.error("❌ No scenarios found. Check data/scenarios.json.")
    else:
        for i, sc in enumerate(scenarios):
            title = sc.get("title", f"Scenario {i+1}")
            desc = sc.get("description", "No description provided.")
            options = sc.get("options", [])

            st.markdown(f"""
            <div class='itype-scenario-card'>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

            st.selectbox(
                "Choose your response:",
                options,
                key=f"sc_{i}"
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("⬅ Back to Questions"):
            st.session_state["step"] = 1
            st.rerun()

    with col3:
        if st.button("Next ➜ See Results"):
            st.session_state["step"] = 3
            st.rerun()


# ============================================================
# STEP 3 — RESULTS
# ============================================================

elif step == 3:

    # Rebuild answers & scenario scores from session state
    if not questions or not archetypes:
        st.error("❌ Missing questions or archetypes configuration.")
    else:
        answers = get_answers_from_state(questions)
        scenario_scores = get_scenario_scores_from_state(scenarios)

        # Calculate button
        calc = st.button("🚀 Calculate My Innovator Type")

        if calc:
            # Step 1: normalize questionnaire scores
            q_scores = normalize_scores(answers)

            # Step 2: combine with scenario scores
            final_scores = combine_with_scenarios(q_scores, scenario_scores)

            # Step 3: determine primary archetype
            primary_name, archetype_data = determine_archetype(final_scores, archetypes)

            # Step 4: Monte Carlo identity spectrum
            probs, stability, shadow = monte_carlo_probabilities(final_scores, archetypes)
            shadow_name, shadow_pct = shadow

            # ----------------------------------------------
            # HERO CARD
            # ----------------------------------------------
            st.markdown(f"""
            <div class='itype-result-card'>
                <h1>{primary_name}</h1>
                <p>{archetype_data.get("description","")}</p>
                <p><b>Stability:</b> {stability:.1f}%</p>
                <p><b>Shadow archetype:</b> {shadow_name} ({shadow_pct:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)

            # ----------------------------------------------
            # RADAR CHART
            # ----------------------------------------------
            st.markdown("<div class='itype-chart-box'>", unsafe_allow_html=True)

            dims = list(final_scores.keys())
            vals = list(final_scores.values())

            radar = go.Figure()
            radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=dims + [dims[0]],
                fill='toself',
                line_color='#00eaff'
            ))
            radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )

            st.plotly_chart(radar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------------------------------------
            # IDENTITY SPECTRUM BAR CHART
            # ----------------------------------------------
            st.markdown("<div class='itype-chart-box'>", unsafe_allow_html=True)

            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[p[0] for p in sorted_probs],
                y=[p[1] for p in sorted_probs],
                marker_color="#00eaff"
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_title="Probability (%)"
            )

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------------------------------------
            # HEATMAP (3×3 GRID)
            # ----------------------------------------------
            st.markdown("<div class='itype-chart-box'>", unsafe_allow_html=True)

            heat_archetypes = [
                ["Visionary", "Strategist", "Storyteller"],
                ["Catalyst", "Apex Innovator", "Integrator"],
                ["Engineer", "Operator", "Experimenter"]
            ]

            heat_values = [
                [probs.get(a, 0) for a in row]
                for row in heat_archetypes
            ]

            heat_fig = go.Figure(data=go.Heatmap(
                z=heat_values,
                x=heat_archetypes[0],
                y=["Row 1", "Row 2", "Row 3"],
                colorscale="blues",
                text=[[f"{a}: {probs.get(a,0):.1f}%" for a in row] for row in heat_archetypes],
                hoverinfo="text",
            ))

            heat_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e5f4ff"),
                title="Identity Heatmap"
            )

            st.plotly_chart(heat_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------------------------------------
            # DETAILED BREAKDOWN
            # ----------------------------------------------
            st.markdown("<hr><h2>Your Innovator Breakdown</h2>", unsafe_allow_html=True)

            st.markdown("<h3>Strengths</h3>", unsafe_allow_html=True)
            for s in archetype_data.get("strengths", []):
                st.markdown(f"<div class='itype-strength-card'>• {s}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='margin-top:20px;'>Growth Edges & Risks</h3>", unsafe_allow_html=True)
            for r in archetype_data.get("risks", []):
                st.markdown(f"<div class='itype-risk-card'>• {r}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='margin-top:20px;'>Recommended Innovation Pathways</h3>", unsafe_allow_html=True)
            for p in archetype_data.get("pathways", []):
                st.markdown(f"<div class='itype-pathway-card'>• {p}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='margin-top:20px;'>Suggested Business Models</h3>", unsafe_allow_html=True)
            for bm in archetype_data.get("business_models", []):
                st.markdown(f"<div class='itype-business-card'>• {bm}</div>", unsafe_allow_html=True)

            st.markdown("<h3 style='margin-top:20px;'>Funding Strategy Fit</h3>", unsafe_allow_html=True)
            for fs in archetype_data.get("funding_strategy", []):
                st.markdown(f"<div class='itype-funding-card'>• {fs}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("⬅ Back to Scenarios"):
            st.session_state["step"] = 2
            st.rerun()

    with col2:
        if st.button("🔄 Start Over"):
            for key in list(st.session_state.keys()):
                if key.startswith("q") or key.startswith("sc_"):
                    del st.session_state[key]
            st.session_state["step"] = 1
            st.rerun()
