import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px

from idix_engine import (
    normalize_scores,
    combine_with_scenarios,
    determine_archetype,
    monte_carlo_probabilities,
    compute_archetype_distances,  # optional for future versions
)

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
# LOAD JSON FILES
# ============================================================

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return default if default is not None else {}

questions = load_json("data/questions.json", default=[])
archetypes = load_json("data/archetypes.json", default={})
scenarios = load_json("data/scenarios.json", default=[])

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
# TAB 1 — QUESTIONNAIRE
# ============================================================

with tabs[0]:
    st.markdown("<h2>Innovation Profile Questionnaire</h2>", unsafe_allow_html=True)

    answers = {}

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

            low_label = q.get("labels", {}).get("low", "Low")
            high_label = q.get("labels", {}).get("high", "High")

            answers[text] = {
                "value": st.slider(
                    label="",
                    min_value=1, max_value=5, value=3,
                    help=f"1 = {low_label}   •   5 = {high_label}",
                    key=f"q{i}"
                ),
                "dimension": dim,
                "reverse": reverse,
            }

# ============================================================
# TAB 2 — SCENARIOS
# ============================================================

with tabs[1]:
    st.markdown("<h2>Scenario-Based Assessment</h2>", unsafe_allow_html=True)

    scenario_scores_accum = {
        "thinking": 0,
        "execution": 0,
        "risk": 0,
        "motivation": 0,
        "team": 0,
        "commercial": 0,
    }
    scenario_count = 0

    if not scenarios:
        st.error("❌ No scenarios found. Check data/scenarios.json.")
    else:
        for i, sc in enumerate(scenarios):

            title = sc.get("title", f"Scenario {i+1}")
            desc = sc.get("description", "No description provided.")

            st.markdown(f"""
            <div class='itype-scenario-card'>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

            options = sc.get("options", ["Option A", "Option B"])
            mapping = sc.get("mapping", {})

            choice = st.selectbox(
                "Choose your response:",
                options,
                key=f"sc{i}"
            )

            score_vec = mapping.get(choice, {
                "thinking": 0, "execution": 0, "risk": 0,
                "motivation": 0, "team": 0, "commercial": 0
            })

            for k in scenario_scores_accum.keys():
                scenario_scores_accum[k] += score_vec.get(k, 0)

            scenario_count += 1

    scenario_scores = (
        {k: scenario_scores_accum[k] / scenario_count for k in scenario_scores_accum}
        if scenario_count > 0
        else scenario_scores_accum.copy()
    )

# ============================================================
# TAB 3 — RESULTS
# ============================================================

with tabs[2]:
    st.markdown("<h2>Your Innovation Profile</h2>", unsafe_allow_html=True)

    calc = st.button("🚀 Calculate My Innovator Type")

    if calc:

        # ----------------------------------------------
        # STEP 1 — Normalize questionnaire scores
        # ----------------------------------------------
        q_scores = normalize_scores(answers)

        # ----------------------------------------------
        # STEP 2 — Combine with scenario scores
        # ----------------------------------------------
        final_scores = combine_with_scenarios(q_scores, scenario_scores)

        # ----------------------------------------------
        # STEP 3 — Determine primary archetype
        # ----------------------------------------------
        primary_name, archetype_data = determine_archetype(final_scores, archetypes)

        if primary_name is None:
            st.error("❌ Could not determine an archetype. Check config.")
            st.stop()

        # ----------------------------------------------
        # STEP 4 — Monte Carlo identity spectrum
        # ----------------------------------------------
        probs, stability, shadow = monte_carlo_probabilities(final_scores, archetypes)
        shadow_name, shadow_pct = shadow

        # ----------------------------------------------
        # HERO CARD
        # ----------------------------------------------
        st.markdown(f"""
        <div class='itype-result-card'>
            <h1>{primary_name}</h1>
            <p>{archetype_data.get("description", "")}</p>
            <div style="margin-top: 10px;">
                <b>Stability:</b> {stability:.1f}%  
                <br>
                <small>
                    Shows how consistently your results remain <b>{primary_name}</b>
                    across 5000 micro-variations.
                </small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ----------------------------------------------
        # TYPE BLEND
        # ----------------------------------------------
        st.markdown("### Your Type Blend")
        st.markdown(f"""
        - 🏆 **Primary archetype:** **{primary_name}**
        - 🌘 **Shadow archetype:** **{shadow_name}** ({shadow_pct:.1f}%)
        """)

        # ----------------------------------------------
        # RADAR CHART
        # ----------------------------------------------
        st.markdown("### Core Innovation Dimensions")
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

        # ----------------------------------------------
        # IDENTITY SPECTRUM (bar chart)
        # ----------------------------------------------
        st.markdown("### Identity Spectrum — Probability Across All Archetypes")

        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        arche_names = [p[0] for p in sorted_probs]
        arche_values = [p[1] for p in sorted_probs]

        spectrum = go.Figure()
        spectrum.add_trace(go.Bar(
            x=arche_names,
            y=arche_values,
            marker_color='#00eaff'
        ))
        spectrum.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_title="Probability (%)",
        )
        st.plotly_chart(spectrum, use_container_width=True)

        # ----------------------------------------------
        # HEATMAP (CORRECTED)
        # ----------------------------------------------
        st.markdown("### 🔥 Identity Heatmap")

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
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e5f4ff"),
            title="Archetype Probability Heatmap"
        )

        st.plotly_chart(heat_fig, use_container_width=True)

        st.markdown("""
        <p style='font-size: 0.9rem; opacity: 0.8;'>
        The heatmap shows your identity cluster. Darker = stronger identity signal.
        </p>
        """, unsafe_allow_html=True)

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

        # ----------------------------------------------
        # EXPLAINER
        # ----------------------------------------------
        st.markdown("<hr><h3>How to Interpret Your Results</h3>", unsafe_allow_html=True)
        st.markdown("""
        - **Stability %** — how consistent your identity is across 5000 simulations.  
        - **Shadow archetype** — second-strongest identity.  
        - **Identity spectrum** — distribution across all archetypes.  
        - **Heatmap** — identity clustering across 3×3 matrix.  
        - **Radar chart** — your core cognitive–behavioural innovation traits.
        """)

