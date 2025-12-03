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
        if info["reverse"]:
            val = 6 - val  # flip slider 1–5 → reverse

        dims[info["dimension"]].append(val)

    final_scores = {}
    for d, values in dims.items():
        if len(values) == 0:
            final_scores[d] = 0
        else:
            avg = sum(values) / len(values)
            final_scores[d] = (avg - 1) / 4 * 100  # convert 1–5 scale → 0–100

    return final_scores


# ============================================================
# INCORPORATE SCENARIO SCORES
# ============================================================

def combine_with_scenarios(question_scores, scenario_scores):
    weights = {
        "questions": 0.75,
        "scenarios": 0.25
    }

    combined = {}
    for dim in question_scores:
        combined[dim] = (
            question_scores[dim] * weights["questions"]
            + scenario_scores[dim] * weights["scenarios"]
        )

    return combined


# ============================================================
# DETERMINE ARCHETYPE
# ============================================================

def determine_archetype(scores, archetypes):
    best_name = None
    best_dist = float("inf")
    best_data = None

    for name, data in archetypes.items():
        sig = data["signature"]

        dist = math.sqrt(sum(
            (scores[k] - sig[k]) ** 2 for k in sig.keys()
        ))

        if dist < best_dist:
            best_dist = dist
            best_name = name
            best_data = data

    return best_name, best_data


# ============================================================
# MONTE CARLO PROBABILITIES (5k simulations)
# ============================================================

def monte_carlo_probabilities(base_scores, archetypes, runs=5000, noise=0.035):
    counts = {name: 0 for name in archetypes.keys()}

    for _ in range(runs):
        pert = {
            dim: max(0, min(100, val + random.gauss(0, val * noise)))
            for dim, val in base_scores.items()
        }

        name, _ = determine_archetype(pert, archetypes)
        counts[name] += 1

    total = sum(counts.values())
    probs = {k: (v / total) * 100 for k, v in counts.items()}

    # stability score = probability of top archetype
    primary = max(probs, key=probs.get)
    stability = probs[primary]

    # shadow = second-highest
    shadow = sorted(probs.items(), key=lambda x: x[1], reverse=True)[1]

    return probs, stability, shadow
