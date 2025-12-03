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

if "open_archetype" not in st.session_state:
    st.session_state["open_archetype"] = None


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
# LOAD JSON
# ============================================================

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

questions = load_json("data/questions.json", [])
archetypes = load_json("data/archetypes.json", {})
scenarios = load_json("data/scenarios.json", [])


# ============================================================
# HERO
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
# STEP BAR
# ============================================================

step = st.session_state["step"]
step_labels = {
    1: "Step 1 of 3 — Innovation Profile Questionnaire",
    2: "Step 2 of 3 — Scenario-Based Assessment",
    3: "Step 3 of 3 — Your Innovator Type & Results",
}

st.markdown(f"### {step_labels[step]}")
st.progress(step / 3)


# ============================================================
# HELPERS
# ============================================================

def get_answers_from_state(questions):
    answers = {}
    for i, q in enumerate(questions):
        answers[q["question"]] = {
            "value": st.session_state.get(f"q{i}", 3),
            "dimension": q["dimension"],
            "reverse": q["reverse"]
        }
    return answers


def get_scenario_scores_from_state(scenarios):
    accum = {k: 0 for k in ["thinking","execution","risk","motivation","team","commercial"]}
    count = 0

    for i, sc in enumerate(scenarios):
        choice = st.session_state.get(f"sc_{i}")
        mapping = sc.get("mapping", {})
        if choice in mapping:
            for k in accum:
                accum[k] += mapping[choice].get(k, 0)
            count += 1

    return {k: accum[k] / count for k in accum} if count else accum


# ============================================================
# STEP 1 — QUESTIONNAIRE
# ============================================================

if step == 1:

    for i, q in enumerate(questions):

        st.markdown(f"""
        <div class='itype-question-card'>
            <h3>{q['question']}</h3>
        </div>
        """, unsafe_allow_html=True)

        st.slider(
            label="",
            min_value=1, max_value=5,
            value=st.session_state.get(f"q{i}", 3),
            key=f"q{i}"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reset"):
            for k in list(st.session_state.keys()):
                if k.startswith("q") or k.startswith("sc_"):
                    del st.session_state[k]
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

    st.markdown("<h2>Scenario-Based Assessment</h2>", unsafe_allow_html=True)

    for i, sc in enumerate(scenarios):

        title = sc["title"]
        desc = sc["description"]
        options = sc["options"]

        # unified tile
        st.markdown(f"""
        <div class="scenario-card">
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='scenario-selectbox'>", unsafe_allow_html=True)

        st.selectbox(
            "Your response:",
            options,
            key=f"sc_{i}",
            label_visibility="collapsed"
        )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='scenario-spacer'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅ Back"):
            st.session_state["step"] = 1
            st.rerun()

    with col3:
        if st.button("Next ➜ Results"):
            st.session_state["step"] = 3
            st.rerun()


# ============================================================
# STEP 3 — RESULTS
# ============================================================

elif step == 3:

    answers = get_answers_from_state(questions)
    scenario_scores = get_scenario_scores_from_state(scenarios)

    if st.button("🚀 Calculate My Innovator Type"):
        
        q_scores = normalize_scores(answers)
        final_scores = combine_with_scenarios(q_scores, scenario_scores)

        primary, data = determine_archetype(final_scores, archetypes)
        probs, stability, shadow = monte_carlo_probabilities(final_scores, archetypes)
        shadow_name, shadow_pct = shadow
        st.session_state["has_results"] = True


        # HERO CARD
        st.markdown(f"""
        <div class='itype-result-card'>
        <h1>{primary}</h1>
        <p>{data['description']}</p>
        <p><b>Stability:</b> {stability:.1f}%</p>
        <p><b>Shadow:</b> {shadow_name} ({shadow_pct:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)


        # RADAR CHART
        dims = list(final_scores.keys())
        vals = list(final_scores.values())

        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=dims + [dims[0]],
            fill='toself',
            line_color="#00eaff"
        ))
        radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(radar, use_container_width=True)

        # BAR CHART — identity spectrum
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

        bar = go.Figure()
        bar.add_trace(go.Bar(
            x=[p[0] for p in sorted_probs],
            y=[p[1] for p in sorted_probs],
            marker_color="#00eaff"
        ))
        bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Probability (%)"
        )
        st.plotly_chart(bar, use_container_width=True)

        # HEATMAP — 3×3 identity matrix
        heat_grid = [
            ["Visionary", "Strategist", "Storyteller"],
            ["Catalyst", "Apex Innovator", "Integrator"],
            ["Engineer", "Operator", "Experimenter"]
        ]

        heat_values = [[probs.get(a,0) for a in row] for row in heat_grid]

        heat = go.Figure(go.Heatmap(
            z=heat_values,
            x=["Visionary", "Strategist", "Storyteller"],
            y=["Cluster 1","Cluster 2","Cluster 3"],
            colorscale="blues",
            text=[[f"{a}: {probs[a]:.1f}%" for a in row] for row in heat_grid],
            hoverinfo="text"
        ))
        heat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            title="Identity Heatmap"
        )
        st.plotly_chart(heat, use_container_width=True)

        # BREAKDOWN
        st.markdown("<hr><h2>Your Innovator Breakdown</h2>", unsafe_allow_html=True)

        st.markdown("### Strengths")
        for s in data.get("strengths", []):
            st.markdown(f"<div class='itype-strength-card'>• {s}</div>", unsafe_allow_html=True)

        st.markdown("### Risks")
        for r in data.get("risks", []):
            st.markdown(f"<div class='itype-risk-card'>• {r}</div>", unsafe_allow_html=True)

        st.markdown("### Pathways")
        for p in data.get("pathways", []):
            st.markdown(f"<div class='itype-pathway-card'>• {p}</div>", unsafe_allow_html=True)

        st.markdown("### Business Models")
        for bm in data.get("business_models", []):
            st.markdown(f"<div class='itype-business-card'>• {bm}</div>", unsafe_allow_html=True)

        st.markdown("### Funding Fit")
        for fs in data.get("funding_strategy", []):
            st.markdown(f"<div class='itype-funding-card'>• {fs}</div>", unsafe_allow_html=True)

    # navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back"):
            st.session_state["step"] = 2
            st.rerun()
    with col2:
        if st.button("🔄 Start Over"):
            for k in list(st.session_state.keys()):
                if k.startswith("q") or k.startswith("sc_"):
                    del st.session_state[k]
            st.session_state["step"] = 1
            st.rerun()


# ============================================================
# ============================================================
# ARCHETYPE LIBRARY — only after CALCULATION & only in Step 3
# ============================================================

if "has_results" in st.session_state and st.session_state["has_results"]:

    st.markdown("<hr class='hr-neon'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Explore All Archetypes</h2>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.85; text-align:center;'>Click any tile to reveal its full profile.</p>", unsafe_allow_html=True)

    # Track open archetype
    if "open_archetype" not in st.session_state:
        st.session_state["open_archetype"] = None

    # 3×3 GRID
    cols = st.columns(3)

    for i, (name, data) in enumerate(archetypes.items()):
        col = cols[i % 3]

        with col:
            active = (st.session_state["open_archetype"] == name)
            tile_class = "archetype-tile active" if active else "archetype-tile"

            # Invisible yet fully clickable button wrapper
            clicked = st.button(
                label=f"""
                <div class="{tile_class}">
                    <h4>{name}</h4>
                </div>
                """,
                key=f"arche_btn_{name}",
                use_container_width=True
            )

            # Force streamlit button to be invisible
            st.markdown(f"""
            <style>
            button[data-testid="baseButton-secondary"][key="arche_btn_{name}"] {{
                background: none !important;
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
            }}
            </style>
            """, unsafe_allow_html=True)

            if clicked:
                # Toggle behaviour
                if st.session_state["open_archetype"] == name:
                    st.session_state["open_archetype"] = None
                else:
                    st.session_state["open_archetype"] = name

    # EXPANDED PANEL
    if st.session_state["open_archetype"]:
        a = st.session_state["open_archetype"]
        info = archetypes[a]

        st.markdown(f"""
        <div class="archetype-panel">
         <h2 style="text-align:center;">{a}</h2>
        <p>{info.get("description","")}</p>

        <h4>Strengths</h4>
        <ul>{''.join([f'<li>{s}</li>' for s in info.get('strengths',[])])}</ul>

        <h4>Risks</h4>
        <ul>{''.join([f'<li>{r}</li>' for r in info.get('risks',[])])}</ul>

        <h4>Pathways</h4>
        <ul>{''.join([f'<li>{p}</li>' for p in info.get('pathways',[])])}</ul>

        <h4>Business Models</h4>
        <ul>{''.join([f'<li>{bm}</li>' for bm in info.get('business_models',[])])}</ul>

        <h4>Funding Strategy Fit</h4>
        <ul>{''.join([f'<li>{fs}</li>' for fs in info.get('funding_strategy',[])])}</ul>
        </div>
        """, unsafe_allow_html=True)
