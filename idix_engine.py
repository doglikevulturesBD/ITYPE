import math

# ============================================================
# IDIX SCORING ENGINE
# ============================================================

def calculate_idix_scores(answers):
    """
    Converts questionnaire responses into normalized 0–100 scores
    for each dimension.

    answers format:
    {
        "Q1": {"value": 4, "dimension": "CRE", "reverse": False},
        "Q2": {"value": 2, "dimension": "ANA", "reverse": True},
        ...
    }
    """

    # Step 1 — accumulate raw values
    dimension_totals = {}
    dimension_counts = {}

    for qid, entry in answers.items():
        dim = entry["dimension"]
        value = entry["value"]

        # Reverse-score if needed (1↔5, 2↔4, 3 stays)
        if entry.get("reverse", False):
            value = 6 - value

        dimension_totals[dim] = dimension_totals.get(dim, 0) + value
        dimension_counts[dim] = dimension_counts.get(dim, 0) + 1

    # Step 2 — convert to 0–100 scale
    scores = {}
    for dim in dimension_totals:
        raw_avg = dimension_totals[dim] / dimension_counts[dim]

        # Convert 1–5 to 0–100
        normalized = (raw_avg - 1) / 4 * 100
        scores[dim] = round(normalized)

    return scores


# ============================================================
# ARCHETYPE MATCHING
# ============================================================

def determine_archetype(scores, archetypes):
    """
    Determines the closest-matching archetype using Euclidean distance.
    This version is SAFE:
    - Skips invalid/missing signatures
    - Skips archetypes missing dimensions
    - Never crashes (returns fallback)
    """

    best_match = None
    lowest_distance = float("inf")

    for archetype_name, data in archetypes.items():

        # -- Validate the signature exists --
        sig = data.get("signature")
        if sig is None:
            print(f"[WARNING] Archetype '{archetype_name}' missing signature → skipped")
            continue

        if not isinstance(sig, dict):
            print(f"[WARNING] Archetype '{archetype_name}' has invalid signature format → skipped")
            continue

        # -- Ensure all dimensions exist in the signature --
        missing_dims = [dim for dim in scores if dim not in sig]
        if missing_dims:
            print(f"[WARNING] Archetype '{archetype_name}' missing dimensions: {missing_dims} → skipped")
            continue

        # -- Compute Euclidean distance --
        try:
            distance = math.sqrt(sum((scores[d] - sig[d]) ** 2 for d in scores))
        except Exception as e:
            print(f"[ERROR] Archetype '{archetype_name}' distance calculation failed: {e}")
            continue

        if distance < lowest_distance:
            lowest_distance = distance
            best_match = archetype_name

    # --------------------------------------------------------
    # SAFETY FALLBACK — no matching archetype
    # --------------------------------------------------------
    if best_match is None:
        print("[WARNING] No valid archetype matched. Returning fallback.")
        return (
            "Undefined Innovator",
            {
                "description": "Your profile does not match any predefined archetype. "
                               "You may represent a new, emerging innovator identity.",
                "strengths": [
                    "Highly unconventional thinking",
                    "Does not fit traditional innovator molds"
                ],
                "risks": [
                    "Your unique profile needs more data to classify properly"
                ]
            }
        )

    return best_match, archetypes[best_match]
