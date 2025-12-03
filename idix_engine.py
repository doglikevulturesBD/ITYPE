import numpy as np

# ============================================================
# IDIX SCORE CALCULATION
# ============================================================

def calculate_idix_scores(answers):
    """
    answers = {
        question: {
            "value": slider value,
            "dimension": "thinking" / "execution" / ...,
            "reverse": bool
        }
    }
    """

    # Initialise dimension buckets
    dimension_totals = {}
    dimension_counts = {}

    for q_text, q_data in answers.items():
        dim = q_data["dimension"]
        val = q_data["value"]

        # Reverse-score if required
        if q_data["reverse"]:
            val = 6 - val   # 1->5, 2->4, 3->3 ...

        dimension_totals[dim] = dimension_totals.get(dim, 0) + val
        dimension_counts[dim] = dimension_counts.get(dim, 0) + 1

    # Average per dimension
    raw_scores = {
        dim: dimension_totals[dim] / dimension_counts[dim]
        for dim in dimension_totals
    }

    # Normalize 1–5 → 0–100
    normalized_scores = {
        dim: int((score - 1) / 4 * 100)
        for dim, score in raw_scores.items()
    }

    return normalized_scores


# ============================================================
# ARCHETYPE MATCHING (IDIX Engine)
# ============================================================

def determine_archetype(scores, archetypes_data):
    """
    scores = { "thinking": XX, "execution": XX, ... }

    archetypes_data = {
        "Architect": {
            "signature": {dim: target score},
            "description": "...",
            "strengths": [...],
            "risks": [...]
        }
    }
    """

    best_name = None
    best_diff = float("inf")

    for name, data in archetypes_data.items():
        signature = data["signature"]

        # Compare user dimensions to archetype signature
        diffs = []
        for dim, target in signature.items():
            diffs.append(abs(scores.get(dim, 0) - target))

        avg_diff = np.mean(diffs)

        if avg_diff < best_diff:
            best_diff = avg_diff
            best_name = name

    return best_name, archetypes_data[best_name]

