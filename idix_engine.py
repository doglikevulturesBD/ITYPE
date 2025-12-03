import math

# ============================================================
# SCORING ENGINE
# ============================================================

def calculate_idix_scores(answers):
    """
    Convert questionnaire answers (1–5 sliders) into normalised
    0–100 dimension scores.

    Parameters
    ----------
    answers : dict
        {
          "question text": {
              "value": int 1–5,
              "dimension": "thinking" | "execution" | ...,
              "reverse": bool
          }
        }

    Returns
    -------
    dict of normalised 0–100 scores per dimension.
    """

    dimension_totals = {}
    dimension_counts = {}

    for q, data in answers.items():
        raw = data["value"]
        dim = data["dimension"]
        reverse = data["reverse"]

        # Reverse score mapping: 1→5, 2→4, 3→3, 4→2, 5→1
        if reverse:
            raw = 6 - raw

        # Convert 1–5 → 0–1 (normalised)
        norm = (raw - 1) / 4

        if dim not in dimension_totals:
            dimension_totals[dim] = 0
            dimension_counts[dim] = 0

        dimension_totals[dim] += norm
        dimension_counts[dim] += 1

    # Convert averages to 0–100 scale
    scores = {}
    for d in dimension_totals:
        avg = dimension_totals[d] / dimension_counts[d]
        scores[d] = round(avg * 100, 2)

    return scores


# ============================================================
# SCENARIO REFINEMENT ENGINE
# ============================================================

def apply_scenario_adjustments(scores, scenario_answers):
    """
    Adjust scores based on scenario selections.
    Each scenario adds a small-but-meaningful uplift to its dimension.

    Parameters
    ----------
    scores : dict
        {"thinking": 54.12, "execution": 71.22, ...}

    scenario_answers : dict
        {
          "scenario_1": "thinking",
          "scenario_2": "execution",
          ...
        }

    Returns
    -------
    updated_scores : dict
        Dimensions slightly boosted based on scenarios.
    """

    # Global scenario influence weight (tunable)
    ADJ = 3  # adds +3 per scenario (max capped at 100)

    for scenario_id, dim in scenario_answers.items():
        if dim in scores:
            scores[dim] = min(scores[dim] + ADJ, 100)

    return scores


# ============================================================
# ARCHETYPE MATCHING ENGINE
# ============================================================

def determine_archetype(scores, archetypes_data):
    """
    Match user dimension scores to archetypes using Euclidean distance.

    Parameters
    ----------
    scores : dict
        {"thinking": 70, "execution": 60, ...}

    archetypes_data : dict
        Format:
        {
          "Visionary": {
              "signature": {
                    "thinking": 90,
                    "execution": 40,
                    "risk": 80,
                    "motivation": 70,
                    "team": 50,
                    "commercial": 40
              },
              "description": "...",
              "strengths": [...],
              "risks": [...],
              "trl_affinity": "...",
              "pathway_suggestions": [...],
              "funding_strategy": [...],
              "business_models": [...]
          },
          ...
        }

    Returns
    -------
    archetype_name : str
    archetype_data : dict
    """

    best_name = None
    best_distance = float("inf")
    best_data = None

    for name, data in archetypes_data.items():
        sig = data["signature"]

        # Compute Euclidean distance between user and archetype signature
        dist_sq = 0
        for dim in scores:
            user_val = scores[dim]
            target_val = sig.get(dim, 50)  # default neutral midpoint
            dist_sq += (user_val - target_val) ** 2

        distance = math.sqrt(dist_sq)

        if distance < best_distance:
            best_distance = distance
            best_name = name
            best_data = data

    return best_name, best_data


# ============================================================
# OPTIONAL — UTILITIES FOR FUTURE FEATURES
# ============================================================

def normalise_signature(signature):
    """
    Convert a 0–100 archetype signature to a unit vector for
    cosine similarity (optional expansion).
    """
    vals = list(signature.values())
    magnitude = math.sqrt(sum(v * v for v in vals))
    return {dim: v / magnitude for dim, v in signature.items()} if magnitude != 0 else signature


def compare_similarity(user_scores, archetype_sig):
    """
    Cosine similarity between user profile and an archetype signature.
    Not used in v1 (Euclidean is better for psychometric profiles),
    but available for future analytics or radar-based scoring.
    """
    dot = sum(user_scores[d] * archetype_sig[d] for d in user_scores)
    mag_user = math.sqrt(sum(v*v for v in user_scores.values()))
    mag_arch = math.sqrt(sum(v*v for v in archetype_sig.values()))
    if mag_user == 0 or mag_arch == 0:
        return 0
    return dot / (mag_user * mag_arch)

