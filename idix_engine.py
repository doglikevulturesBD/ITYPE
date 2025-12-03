import math
import random

# ============================================================
# NORMALISE RAW SCORES (0–100)
# ============================================================

def normalize_scores(raw_answers):
    dims = {
        "thinking": [],
        "execution": [],
        "risk": [],
        "motivation": [],
        "team": [],
        "commercial": []
    }

    for q, info in raw_answers.items():
        val = info["value"]
        if info.get("reverse", False):
            val = 6 - val  # reverse 1–5

        dims[info["dimension"]].append(val)

    final_scores = {}
    for d, values in dims.items():
        if not values:
            final_scores[d] = 0
        else:
            avg = sum(values) / len(values)
            final_scores[d] = ((avg - 1) / 4) * 100  # 0–100

    return final_scores


# ============================================================
# NORMALISE SCENARIO SCORES (0–100)
# ============================================================

def normalize_scenario_scores(scenario_scores_raw):
    # scenario scores often 0–3 → upscale to 0–100
    MAX_SCENARIO = 3  # adjust if using bigger scenario vectors

    normalized = {}
    for k, val in scenario_scores_raw.items():
        normalized[k] = (val / MAX_SCENARIO) * 100 if MAX_SCENARIO > 0 else 0

    return normalized


# ============================================================
# COMBINE QUESTIONNAIRE + SCENARIOS
# ============================================================

def combine_with_scenarios(question_scores, scenario_scores):
    weights = {
        "questions": 0.75,
        "scenarios": 0.25
    }

    # normalise scenario scores into the same 0–100 space
    scenario_norm = normalize_scenario_scores(scenario_scores)

    combined = {}
    for dim in question_scores:
        combined[dim] = (
            question_scores[dim] * weights["questions"]
            + scenario_norm[dim] * weights["scenarios"]
        )

    return combined


# ============================================================
# EUCLIDEAN MATCHING FOR ARCHETYPE
# ============================================================

def determine_archetype(scores, archetypes):
    best_name = None
    best_dist = float("inf")
    best_data = None

    for name, data in archetypes.items():
        sig = data["signature"]

        # safe: intersect keys to prevent KeyError
        keys = set(scores.keys()) & set(sig.keys())

        dist = math.sqrt(sum(
            (scores[k] - sig[k]) ** 2 for k in keys
        ))

        if dist < best_dist:
            best_dist = dist
            best_name = name
            best_data = data

    return best_name, best_data


# ============================================================
# MONTE CARLO PROBABILITIES (IMPROVED)
# ============================================================

def monte_carlo_probabilities(base_scores, archetypes, runs=5000, noise=0.08):
    """
    noise = ±8% of full scale (0–100), not score-dependent.
    Provides consistent, fair perturbation across all dimensions.
    """

    counts = {name: 0 for name in archetypes.keys()}

    for _ in range(runs):
        pert = {}

        for dim, val in base_scores.items():
            # add random gaussian noise (mean 0, sd = noise * 100)
            delta = random.gauss(0, noise * 100)
            pert[dim] = max(0, min(100, val + delta))

        name, _ = determine_archetype(pert, archetypes)
        counts[name] += 1

    total = sum(counts.values())
    probs = {k: (v / total) * 100 for k, v in counts.items()}

    # Primary
    primary = max(probs, key=probs.get)
    stability = probs[primary]

    # Shadow
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    shadow = sorted_probs[1] if len(sorted_probs) > 1 else ("None", 0)

    return probs, stability, shadow
