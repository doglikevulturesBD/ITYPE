import math

# ============================================================
# NORMALISATION AND SCORING UTILITIES
# ============================================================

def normalize_dimension(total, count):
    """
    Takes accumulated dimension total and number of items.
    Returns a normalized 0–100 score.
    """
    if count == 0:
        return 50  # neutral fallback
    raw_avg = total / count  # 1–5
    return (raw_avg - 1) / 4 * 100  # convert to 0–100


# ============================================================
# MAIN IDIX CALCULATION (QUESTIONS ONLY)
# ============================================================

def calculate_question_scores(answers):
    """
    Calculates dimension-level scores from question responses.
    answers is a dict:
       question: {value: int, dimension: str, reverse: bool}
    """

    totals = {}
    counts = {}

    for q, data in answers.items():
        dim = data["dimension"]
        val = data["value"]

        if data.get("reverse", False):
            val = 6 - val  # reverse score

        if dim not in totals:
            totals[dim] = 0
            counts[dim] = 0

        totals[dim] += val
        counts[dim] += 1

    scores = {dim: normalize_dimension(totals[dim], counts[dim]) for dim in totals}
    return scores


# ============================================================
# SCENARIO ENGINE (OPTIONAL INPUT)
# ============================================================

def calculate_scenario_scores(scenario_responses, scenario_weights):
    """
    scenario_responses: list of {impact:1–5 or None}
    scenario_weights:   list of {dimension, weight}

    Returns dimension deltas (positive or negative).
    """

    dimension_adjustments = {}

    for resp, w in zip(scenario_responses, scenario_weights):

        # skip unanswered scenarios
        if resp is None:
            continue

        dim = w["dimension"]
        weight = w["weight"]

        # Convert scenario response 1–5 → -2 to +2
        influence = (resp - 3) * weight

        if dim not in dimension_adjustments:
            dimension_adjustments[dim] = 0

        dimension_adjustments[dim] += influence

    return dimension_adjustments


# ============================================================
# MERGE QUESTION SCORES + SCENARIO ADJUSTMENTS
# ============================================================

def merge_scores(base_scores, scenario_adjustments):
    """
    Adds scenario adjustments into 0–100 scores.
    Clamps between 0 and 100.
    """

    final = {}

    for dim, base_val in base_scores.items():
        adj = scenario_adjustments.get(dim, 0)
        final_val = base_val + adj

        # clamp for safety
        final_val = max(0, min(100, final_val))
        final[dim] = final_val

    return final


# ============================================================
# PRIMARY + SECONDARY ARCHETYPE ENGINE
# ============================================================

def determine_archetypes(scores, archetypes):
    """
    Returns:
      (PrimaryName, PrimaryData), (SecondaryName, SecondaryData)

    Uses Euclidean distance in n-dim vector space.
    """

    distances = []

    for name, data in archetypes.items():

        sig = data.get("signature")

        # Skip invalid archetypes
        if not isinstance(sig, dict):
            continue

        # Skip if signature missing any dimension
        if any(dim not in sig for dim in scores):
            continue

        # Euclidean distance
        dist = sum((scores[d] - sig[d]) ** 2 for d in scores)
        distances.append((name, dist))

    # No valid archetypes? Fail-safe
    if len(distances) == 0:
        return (
            ("Unknown", {
                "description": "Your profile does not align with any archetype yet.",
                "strengths": [],
                "risks": []
            }),
            ("None", {})
        )

    # sort by closeness
    distances.sort(key=lambda x: x[1])

    primary_name = distances[0][0]
    primary_data = archetypes[primary_name]

    if len(distances) > 1:
        shadow_name = distances[1][0]
        shadow_data = archetypes[shadow_name]
    else:
        shadow_name, shadow_data = "None", {}

    return (primary_name, primary_data), (shadow_name, shadow_data)


# ============================================================
# MASTER PIPELINE — CALL FROM STREAMLIT
# ============================================================

def compute_idix(answers, scenario_responses=None, scenario_weights=None, archetypes=None):
    """
    One-call function used by Streamlit:
        1) Score question responses
        2) Apply scenario adjustments (if any)
        3) Compute primary + secondary archetypes
        4) Return everything
    """

    # base question scores
    q_scores = calculate_question_scores(answers)

    # scenario section optional
    if scenario_responses and scenario_weights:
        scenario_adj = calculate_scenario_scores(scenario_responses, scenario_weights)
    else:
        scenario_adj = {}

    # merge
    final_scores = merge_scores(q_scores, scenario_adj)

    # determine types
    if archetypes:
        (p_name, p_data), (s_name, s_data) = determine_archetypes(final_scores, archetypes)
    else:
        (p_name, p_data), (s_name, s_data) = ("Unknown", {}), ("None", {})

    return final_scores, (p_name, p_data), (s_name, s_data)
