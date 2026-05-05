from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
from logic import (
    add_workout, load_workouts, save_workouts,
    summary_by_type, compare_recent_to_past,
    consistency_score, predict_2k,
    total_distance, best_split, average_split,
    VALID_TYPES, format_split
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/workouts", methods=["GET"])
def get_workouts():
    # Return all workouts newest-first so the history tab shows recent entries at the top
    workouts = load_workouts()
    workouts_sorted = sorted(workouts, key=lambda w: w["date"], reverse=True)
    return jsonify(workouts_sorted)


@app.route("/api/workouts", methods=["POST"])
def post_workout():
    workouts = load_workouts()
    data = request.get_json()

    # Reject early if any required field is missing
    required = ["date", "type", "distance_m", "avg_split_sec", "stroke_rate"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Coerce numeric fields; surface a clear error if they aren't castable
    try:
        distance_m = int(data["distance_m"])
        avg_split_sec = int(data["avg_split_sec"])
        stroke_rate = int(data["stroke_rate"])
    except (ValueError, TypeError):
        return jsonify({"error": "distance_m, avg_split_sec, stroke_rate must be integers"}), 400

    added = add_workout(
        workouts,
        data["date"],
        data["type"],
        distance_m,
        avg_split_sec,
        stroke_rate,
        data.get("notes", "")
    )

    if not added:
        return jsonify({"error": "Invalid workout data. Check date format (YYYY-MM-DD) and workout type."}), 400

    save_workouts(workouts)
    return jsonify({"message": "Workout added successfully"}), 201


@app.route("/api/workouts/<int:index>", methods=["DELETE"])
def delete_workout(index):
    # Index refers to position in the sorted (newest-first) list shown in the UI
    # We match by value rather than raw list index to stay in sync with the sorted view
    workouts = load_workouts()
    workouts_sorted = sorted(workouts, key=lambda w: w["date"], reverse=True)

    if index < 0 or index >= len(workouts_sorted):
        return jsonify({"error": "Workout not found"}), 404

    target = workouts_sorted[index]
    workouts = [w for w in workouts if w != target]
    save_workouts(workouts)
    return jsonify({"message": "Workout deleted"})


@app.route("/api/dashboard")
def get_dashboard():
    workouts = load_workouts()

    # Return zeroed-out shape so the frontend doesn't have to handle None
    if not workouts:
        return jsonify({
            "total_distance_m": 0,
            "total_workouts": 0,
            "best_split": None,
            "consistency": None,
            "predict_2k": None,
            "split_trend": [],
            "distance_by_type": {},
            "progress_message": None,
        })

    # Last 12 workouts in chronological order drive the split trend chart
    trend_workouts = sorted(workouts, key=lambda w: w["date"])[-12:]
    split_trend = [
        {
            "date": w["date"],
            "split_sec": w["avg_split_sec"],
            "split_fmt": format_split(w["avg_split_sec"]),
            "type": w["type"],
            "distance_m": w["distance_m"],
        }
        for w in trend_workouts
    ]

    # Only include types that have at least one workout so the bar chart stays clean
    distance_by_type = {}
    for t in VALID_TYPES:
        d = total_distance(workouts, t)
        if d > 0:
            distance_by_type[t] = d

    best = best_split(workouts)
    best_data = None
    if best:
        best_data = {
            "split_fmt": format_split(best["avg_split_sec"]),
            "date": best["date"],
            "type": best["type"],
        }

    score = consistency_score(workouts)
    pred = predict_2k(workouts)
    progress = compare_recent_to_past(workouts)

    # Monthly stats are scoped by calendar month prefix so no timezone math is needed
    now = datetime.now()
    month_prefix = now.strftime("%Y-%m")
    monthly = [w for w in workouts if w["date"].startswith(month_prefix)]
    monthly_distance = total_distance(monthly)
    monthly_count = len(monthly)

    return jsonify({
        "total_distance_m": total_distance(workouts),
        "monthly_distance_m": monthly_distance,
        "monthly_workouts": monthly_count,
        "total_workouts": len(workouts),
        "best_split": best_data,
        "consistency": round(score, 1) if score is not None else None,
        "predict_2k": pred,
        "split_trend": split_trend,
        "distance_by_type": distance_by_type,
        "progress_message": progress,
    })


@app.route("/api/summary")
def get_summary():
    # Builds one card per workout type; skips types with no data
    workouts = load_workouts()
    result = []

    for t in VALID_TYPES:
        from logic import filter_by_type, average_stroke_rate
        filtered = filter_by_type(workouts, t)
        if filtered:
            avg = average_split(workouts, t)
            rate = average_stroke_rate(workouts, t)
            best = best_split(workouts, t)
            dist = total_distance(workouts, t)
            result.append({
                "type": t,
                "count": len(filtered),
                "total_distance_m": dist,
                "avg_split_fmt": format_split(avg) if avg else None,
                "avg_stroke_rate": round(rate, 1) if rate else None,
                "best_split_fmt": format_split(best["avg_split_sec"]) if best else None,
                "best_split_date": best["date"] if best else None,
            })

    return jsonify(result)


@app.route("/api/sample", methods=["POST"])
def load_sample():
    # Appends (not replaces) sample workouts so existing data is preserved
    workouts = load_workouts()

    sample_workouts = [
        ["2026-03-01", "steady_state", 12000, 132, 20, "early season base"],
        ["2026-03-05", "steady_state", 10000, 131, 20, "focused on technique"],
        ["2026-03-08", "interval", 4000, 122, 28, "4x1000m, first intervals"],
        ["2026-03-12", "steady_state", 12000, 130, 20, "felt strong"],
        ["2026-03-15", "cross_training", 3600, 145, 18, "light cross training"],
        ["2026-03-19", "interval", 3000, 120, 29, "6x500m"],
        ["2026-03-22", "steady_state", 14000, 129, 20, "long row"],
        ["2026-03-26", "interval", 4000, 118, 29, "4x1000m, better pacing"],
        ["2026-04-01", "steady_state", 12000, 128, 20, "strong session"],
        ["2026-04-05", "interval", 3000, 117, 30, "6x500m felt fast"],
        ["2026-04-09", "steady_state", 12000, 127, 20, "new steady state pb"],
        ["2026-04-12", "test_piece", 2000, 119, 31, "practice 2k race"],
        ["2026-04-15", "interval", 4000, 116, 30, "4x1000m — best session"],
        ["2026-04-18", "steady_state", 10000, 126, 20, "taper"],
        ["2026-04-20", "test_piece", 2000, 117, 32, "2k time trial — pb"],
    ]

    for w in sample_workouts:
        add_workout(workouts, w[0], w[1], w[2], w[3], w[4], w[5])

    save_workouts(workouts)
    return jsonify({"message": f"Loaded {len(sample_workouts)} sample workouts"})


@app.route("/api/clear", methods=["POST"])
def clear_data():
    # Saves an empty list, effectively wiping the data file
    save_workouts([])
    return jsonify({"message": "All data cleared"})


if __name__ == "__main__":
    app.run(debug=True)
