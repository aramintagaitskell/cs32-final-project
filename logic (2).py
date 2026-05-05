import json
from datetime import datetime

DATA_FILE = "workouts.json"

VALID_TYPES = ["steady_state", "interval", "test_piece", "cross_training"]


def format_split(seconds):
    # Convert raw seconds to m:ss string (e.g. 130 → "2:10")
    seconds = round(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02}"


def parse_split(split_text):
    # Returns total seconds from "m:ss" input; None if malformed or out of range
    try:
        minutes, seconds = split_text.split(":")
        minutes = int(minutes)
        seconds = int(seconds)
        if minutes < 0 or seconds < 0 or seconds >= 60:
            raise ValueError
        return minutes * 60 + seconds
    except ValueError:
        return None


def valid_date(date_text):
    # Strict ISO date check; rejects anything that isn't YYYY-MM-DD
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def save_workouts(workouts):
    # Overwrites the JSON file with the current in-memory list
    with open(DATA_FILE, "w") as f:
        json.dump(workouts, f, indent=4)


def load_workouts():
    # Returns an empty list instead of crashing when no file exists yet
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def add_workout(workouts, date, workout_type, distance_m, avg_split_sec, stroke_rate, notes):
    # Guards against bad data before appending; mutates the list in place
    if not valid_date(date):
        return False
    if workout_type not in VALID_TYPES:
        return False
    if distance_m <= 0 or avg_split_sec <= 0 or stroke_rate <= 0:
        return False

    workout = {
        "date": date,
        "type": workout_type,
        "distance_m": distance_m,
        "avg_split_sec": avg_split_sec,
        "stroke_rate": stroke_rate,
        "notes": notes,
    }
    workouts.append(workout)
    return True


def filter_by_type(workouts, workout_type):
    # Simple type filter; used by all aggregate functions to scope their data
    return [w for w in workouts if w["type"] == workout_type]


def average_split(workouts, workout_type=None):
    # Mean split across all workouts, or just one type if specified
    filtered = filter_by_type(workouts, workout_type) if workout_type else workouts
    if not filtered:
        return None
    return sum(w["avg_split_sec"] for w in filtered) / len(filtered)


def average_stroke_rate(workouts, workout_type=None):
    filtered = filter_by_type(workouts, workout_type) if workout_type else workouts
    if not filtered:
        return None
    return sum(w["stroke_rate"] for w in filtered) / len(filtered)


def total_distance(workouts, workout_type=None):
    filtered = filter_by_type(workouts, workout_type) if workout_type else workouts
    return sum(w["distance_m"] for w in filtered)


def best_split(workouts, workout_type=None):
    # Returns the full workout dict with the lowest (fastest) split value
    filtered = filter_by_type(workouts, workout_type) if workout_type else workouts
    if not filtered:
        return None
    return min(filtered, key=lambda w: w["avg_split_sec"])


def summary_by_type(workouts):
    # Builds a per-type stats dict; omits types with no recorded workouts
    result = {}
    for t in VALID_TYPES:
        filtered = filter_by_type(workouts, t)
        if filtered:
            avg = average_split(workouts, t)
            rate = average_stroke_rate(workouts, t)
            best = best_split(workouts, t)
            dist = total_distance(workouts, t)
            result[t] = {
                "count": len(filtered),
                "total_distance_m": dist,
                "avg_split_fmt": format_split(avg),
                "avg_stroke_rate": round(rate, 1),
                "best_split_fmt": format_split(best["avg_split_sec"]),
                "best_split_date": best["date"],
            }
    return result


def compare_recent_to_past(workouts, workout_type=None):
    # Compares mean split of last 3 workouts vs the 3 before them
    # Negative diff means slower; positive means improving
    filtered = filter_by_type(workouts, workout_type) if workout_type else workouts
    if len(filtered) < 6:
        return "Need at least 6 workouts to compare recent progress."
    filtered = sorted(filtered, key=lambda w: w["date"])
    previous = filtered[-6:-3]
    recent = filtered[-3:]
    previous_avg = sum(w["avg_split_sec"] for w in previous) / 3
    recent_avg = sum(w["avg_split_sec"] for w in recent) / 3
    diff = previous_avg - recent_avg
    if diff > 0:
        return f"Your last 3 workouts are {abs(diff):.1f}s faster per 500m than the previous 3. You're improving."
    elif diff < 0:
        return f"Your last 3 workouts are {abs(diff):.1f}s slower per 500m than the previous 3."
    else:
        return "Your recent average split is the same as the previous 3 workouts."


def consistency_score(workouts, workout_type=None):
    # Mean absolute deviation of splits from the overall average
    # Lower score = more consistent pacing across sessions
    filtered = filter_by_type(workouts, workout_type) if workout_type else workouts
    if len(filtered) < 2:
        return None
    avg = average_split(filtered)
    diffs = [abs(w["avg_split_sec"] - avg) for w in filtered]
    return sum(diffs) / len(diffs)


def predict_2k(workouts):
    # Estimates 2k race time from recent interval/test-piece data
    # Test pieces are weighted 1.5x because they better reflect race effort
    # Adds a 2s fatigue buffer, then multiplies split by 4 (2000m / 500m)
    useful = [
        w for w in workouts
        if w["type"] in ("interval", "test_piece")
    ]

    if len(useful) < 3:
        return {
            "available": False,
            "message": "Need at least 3 interval or test-piece workouts to estimate 2k time.",
        }

    useful = sorted(useful, key=lambda w: w["date"])
    recent = useful[-3:]

    weights = []
    for w in recent:
        if w["type"] == "test_piece":
            weights.append(1.5)
        else:
            weights.append(1.0)

    total_weight = sum(weights)
    weighted_split = sum(w["avg_split_sec"] * wt for w, wt in zip(recent, weights)) / total_weight
    weighted_rate = sum(w["stroke_rate"] * wt for w, wt in zip(recent, weights)) / total_weight

    predicted_split_sec = weighted_split + 2
    predicted_time_sec = predicted_split_sec * 4

    return {
        "available": True,
        "predicted_split_fmt": format_split(predicted_split_sec),
        "predicted_split_sec": round(predicted_split_sec, 1),
        "predicted_time_fmt": format_split(predicted_time_sec),
        "predicted_time_sec": round(predicted_time_sec, 1),
        "avg_stroke_rate": round(weighted_rate, 1),
        "based_on": len(recent),
        "note": "Estimate only. Real 2k performance depends on race plan, fatigue, and consistency.",
    }
