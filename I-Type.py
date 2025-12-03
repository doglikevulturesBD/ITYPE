import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px

from idix_engine import (
    normalize_scores,
    combine_with_scenarios,
    determine_archetype,
    monte_carlo_probabilities,
)

# ============================================================
# SESSION STATE INIT
# ============================================================

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "assessment"


# ============================================================
# LOAD CSS
# ============================================================

def load_css():
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        st.warning("⚠ Missing CSS file — assets/styles.css")

load_css()


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
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
# TABS
# ============================================================

tab_assess, tab_scenario, tab_results, tab_dev = st.tabs(
    ["🔍 Assessment", "🧪 Scenarios", "📊 Results", "DEV"]
)


# ============================================================
# TAB 1 — QUESTIONNAIRE
# ============================================================

with tab_assess:

    # If user switched tabs, stop rendering this tab
    if st.session_state["active_tab"] != "assessment":
        st.stop()

    st.markdown("<h2>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)

    answers = {}

    if not questions:
        st.error("❌ questions.json missing or empty.")
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

            answers[text] = {
                "value": st.slider("", 1, 5, 3, key=f"q{i}"),
                "dimension": dim,
                "reverse": reverse
            }

    # --------------------------------------------------------
    # NAVIGATION BUTTONS
    # --------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➡ Go to Scenarios"):
            st.session_state["active_tab"] = "scenarios"
            st.experimental_rerun()

    with col2:
        if st.button("📊 Skip to Results"):
            st.session_state["active_tab"] = "results"
            st.experimental_rerun()


# ============================================================
# TAB 2 — SCENARIOS
# ============================================================

with tab_scenario:

    if st.session_state["active_tab"] != "scenarios":
        st.stop()

    st.markdown("<h2>Scenario-Based Assessment</h2>", unsafe_allow_html=True)

    scenario_scores_accum = {
        "thinking": 0, "execution": 0, "risk": 0,
        "motivation": 0, "team": 0, "commercial": 0
    }
    scenario_count = 0

    for i, sc in enumerate(scenarios):

        title = sc.get("title", f"Scenario {i+1}")
        desc = sc.get("description", "")

        st.markdown(f"""
        <div class='itype-scenario-card'>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

        choice = st.selectbox(
            "Choose your response:",
            sc.get("options", []),
            key=f"sc_{i}"
        )

        mapping = sc.get("mapping", {})
        scores = mapping.get(choice, {})

        for k in scenario_scores_accum:
            scenario_scores_accum[k] += scores.get(k, 0)

        scenario_count += 1

    scenario_scores = {
        k: scenario_scores_accum[k] / max(1, scenario_count)
        for k in scenario_scores_accum
    }

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📊 See Results"):
        st.session_state["active_tab"] = "results"
        st.experimental_rerun()


# ============================================================
# TAB 3 — RESULTS
# ============================================================

with tab_results:

    if st.session_state["active_tab"] != "results":
        st.stop()

    st.markdown("<h2>Your Innovation Profile</h2>", unsafe_allow_html=True)

    if st.button("🚀 Calculate My Innovator Type"):

        q_scores = normalize_scores(answers)
        final_scores = combine_with_scenarios(q_scores, scenario_scores)
        primary_name, archetype_data = determine_archetype(final_scores, archetypes)

        probs, stability, shadow = monte_carlo_probabilities(final_scores, archetypes)
        shadow_name, shadow_pct = shadow

        # ----------------------------------------------------
        # RESULT CARD
        # ----------------------------------------------------
        st.markdown(f"""
        <div class='itype-result-card'>
            <h1>{primary_name}</h1>
            <p>{archetype_data.get("description","")}</p>
            <p><b>Stability:</b> {stability:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

        # ----------------------------------------------------
        # RADAR
        # ----------------------------------------------------
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
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )

        st.plotly_chart(radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # IDENTITY SPECTRUM
        # ----------------------------------------------------
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

        st.markdown("<div class='itype-chart-box'>", unsafe_allow_html=True)

        fig = go.Figure(go.Bar(
            x=[p[0] for p in sorted_probs],
            y=[p[1] for p in sorted_probs],
            marker_color="#00eaff"
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # HEATMAP (NEON GRID)
        # ----------------------------------------------------
        heat_grid = [
            ["Visionary", "Strategist", "Storyteller"],
            ["Catalyst", "Apex Innovator", "Integrator"],
            ["Engineer", "Operator", "Experimenter"]
        ]

        heat_values = [[probs.get(a,0) for a in row] for row in heat_grid]

        st.markdown("<div class='itype-chart-box'>", unsafe_allow_html=True)

        heatmap = go.Figure(data=go.Heatmap(
            z=heat_values,
            x=heat_grid[0],
            y=["Row 1", "Row 2", "Row 3"],
            colorscale="blues",
            hoverinfo="text",
            text=[[f"{a}: {probs.get(a,0):.1f}%" for a in row] for row in heat_grid]
        ))

        heatmap.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e5f4ff"),
            title="Identity Heatmap"
        )

        st.plotly_chart(heatmap, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TAB 4 — DEVELOPER SIMULATION
# ============================================================

with tab_dev:

    st.markdown("<div class='dev-box'>", unsafe_allow_html=True)

    st.write("Run random simulations to test archetype distributions.")

    if st.button("Run 5000 Simulation"):
        import random
        counts = {k: 0 for k in archetypes}

        for _ in range(5000):
            random_scores = {
                "thinking": random.uniform(0,100),
                "execution": random.uniform(0,100),
                "risk": random.uniform(0,100),
                "motivation": random.uniform(0,100),
                "team": random.uniform(0,100),
                "commercial": random.uniform(0,100),
            }
            name, _ = determine_archetype(random_scores, archetypes)
            counts[name] += 1

        sim_percent = {k: counts[k] / 5000 * 100 for k in counts}

        st.write(sim_percent)

        fig = go.Figure(go.Bar(
            x=list(sim_percent.keys()),
            y=list(sim_percent.values()),
            marker_color="#00eaff"
        ))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
