import json
from datetime import datetime

DATA_FILE = "workouts.json"

VALID_TYPES = ["steady_state", "interval", "test_piece", "cross_training"]


def format_split(seconds):
    seconds = round(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02}"


def parse_split(split_text):
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
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def save_workouts(workouts):
    with open(DATA_FILE, "w") as f:
        json.dump(workouts, f, indent=4)


def load_workouts():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def add_workout(workouts, date, workout_type, distance_m, avg_split_sec, stroke_rate, notes):
    if not valid_date(date):
        print("Invalid date. Use YYYY-MM-DD.")
        return False

    if workout_type not in VALID_TYPES:
        print("Invalid workout type.")
        return False

    if distance_m <= 0 or avg_split_sec <= 0 or stroke_rate <= 0:
        print("Distance, split, and stroke rate must be positive.")
        return False

    workout = {
        "date": date,
        "type": workout_type,
        "distance_m": distance_m,
        "avg_split_sec": avg_split_sec,
        "stroke_rate": stroke_rate,
        "notes": notes
    }

    workouts.append(workout)
    return True


def add_workout_from_user(workouts):
    print("\nAdd a new workout")
    print("-" * 30)

    date = input("Date (YYYY-MM-DD): ").strip()

    print("\nWorkout types:")
    for t in VALID_TYPES:
        print(f"- {t}")

    workout_type = input("Workout type: ").strip().lower()

    try:
        distance_m = int(input("Distance in meters: "))
    except ValueError:
        print("Distance must be a number.")
        return

    split_text = input("Average split per 500m (example 2:12): ").strip()
    avg_split_sec = parse_split(split_text)

    if avg_split_sec is None:
        print("Invalid split. Use m:ss format, like 2:12.")
        return

    try:
        stroke_rate = int(input("Stroke rate: "))
    except ValueError:
        print("Stroke rate must be a number.")
        return

    notes = input("Notes: ").strip()

    added = add_workout(
        workouts,
        date,
        workout_type,
        distance_m,
        avg_split_sec,
        stroke_rate,
        notes
    )

    if added:
        save_workouts(workouts)
        print("Workout added and saved.")


def display_workouts(workouts):
    if not workouts:
        print("\nNo workouts logged yet.")
        return

    sorted_workouts = sorted(workouts, key=lambda w: w["date"])

    print("\nWorkout History")
    print("=" * 40)

    for workout in sorted_workouts:
        print(f"Date: {workout['date']}")
        print(f"Type: {workout['type']}")
        print(f"Distance: {workout['distance_m']} meters")
        print(f"Avg Split: {format_split(workout['avg_split_sec'])}")
        print(f"Stroke Rate: {workout['stroke_rate']}")
        print(f"Notes: {workout['notes']}")
        print("-" * 40)


def filter_by_type(workouts, workout_type):
    return [w for w in workouts if w["type"] == workout_type]


def average_split(workouts, workout_type=None):
    filtered = workouts

    if workout_type:
        filtered = filter_by_type(workouts, workout_type)

    if not filtered:
        return None

    return sum(w["avg_split_sec"] for w in filtered) / len(filtered)


def average_stroke_rate(workouts, workout_type=None):
    filtered = workouts

    if workout_type:
        filtered = filter_by_type(workouts, workout_type)

    if not filtered:
        return None

    return sum(w["stroke_rate"] for w in filtered) / len(filtered)


def total_distance(workouts, workout_type=None):
    filtered = workouts

    if workout_type:
        filtered = filter_by_type(workouts, workout_type)

    return sum(w["distance_m"] for w in filtered)


def best_split(workouts, workout_type=None):
    filtered = workouts

    if workout_type:
        filtered = filter_by_type(workouts, workout_type)

    if not filtered:
        return None

    return min(filtered, key=lambda w: w["avg_split_sec"])


def summary_by_type(workouts):
    if not workouts:
        print("No workouts to summarize.")
        return

    print("\nSummary by Workout Type")
    print("=" * 40)

    for workout_type in VALID_TYPES:
        filtered = filter_by_type(workouts, workout_type)

        if filtered:
            avg = average_split(workouts, workout_type)
            rate = average_stroke_rate(workouts, workout_type)
            best = best_split(workouts, workout_type)
            distance = total_distance(workouts, workout_type)

            print(f"\nWorkout type: {workout_type}")
            print(f"Number of workouts: {len(filtered)}")
            print(f"Total distance: {distance} meters")
            print(f"Average split: {format_split(avg)}")
            print(f"Average stroke rate: {rate:.1f}")
            print(f"Best split: {format_split(best['avg_split_sec'])} on {best['date']}")


def compare_recent_to_past(workouts, workout_type=None):
    filtered = workouts

    if workout_type:
        filtered = filter_by_type(workouts, workout_type)

    if len(filtered) < 6:
        return "Need at least 6 workouts to compare recent progress."

    filtered = sorted(filtered, key=lambda w: w["date"])

    previous = filtered[-6:-3]
    recent = filtered[-3:]

    previous_avg = sum(w["avg_split_sec"] for w in previous) / 3
    recent_avg = sum(w["avg_split_sec"] for w in recent) / 3

    difference = previous_avg - recent_avg

    if difference > 0:
        return f"Your last 3 workouts are {difference:.1f} seconds faster per 500m than the previous 3."
    elif difference < 0:
        return f"Your last 3 workouts are {abs(difference):.1f} seconds slower per 500m than the previous 3."
    else:
        return "Your recent average split has stayed the same."


def consistency_score(workouts, workout_type=None):
    filtered = workouts

    if workout_type:
        filtered = filter_by_type(workouts, workout_type)

    if len(filtered) < 2:
        return None

    avg = average_split(filtered)
    differences = [abs(w["avg_split_sec"] - avg) for w in filtered]

    return sum(differences) / len(differences)


def predict_2k(workouts):
    useful_workouts = [
        w for w in workouts
        if w["type"] == "interval" or w["type"] == "test_piece"
    ]

    if len(useful_workouts) < 3:
        return "Need at least 3 interval or test piece workouts to estimate 2k."

    useful_workouts = sorted(useful_workouts, key=lambda w: w["date"])
    recent = useful_workouts[-3:]

    avg_recent_split = sum(w["avg_split_sec"] for w in recent) / len(recent)
    avg_recent_rate = sum(w["stroke_rate"] for w in recent) / len(recent)

    predicted_split = avg_recent_split + 2
    predicted_time = predicted_split * 4

    return (
        f"Estimated 2k split: {format_split(predicted_split)}\n"
        f"Estimated 2k time: {format_split(predicted_time)}\n"
        f"Based on your 3 most recent interval/test-piece workouts.\n"
        f"Average stroke rate in those workouts: {avg_recent_rate:.1f}\n"
        "This is only an estimate because real 2k performance also depends on fatigue, race plan, consistency, and workout type."
    )


def choose_workout_type():
    print("\nChoose workout type:")
    print("all")
    for t in VALID_TYPES:
        print(t)

    choice = input("Choice: ").strip().lower()

    if choice == "all":
        return None

    if choice in VALID_TYPES:
        return choice

    print("Invalid workout type.")
    return "invalid"


def add_sample_data(workouts):
    sample_workouts = [
        ["2026-04-01", "steady_state", 12000, 132, 20, "felt strong"],
        ["2026-04-03", "interval", 4000, 118, 28, "4x1000m"],
        ["2026-04-06", "steady_state", 10000, 130, 20, "more efficient"],
        ["2026-04-08", "steady_state", 12000, 129, 20, "solid session"],
        ["2026-04-10", "steady_state", 12000, 128, 20, "best steady state this week"],
        ["2026-04-12", "interval", 3000, 117, 30, "6x500m"],
        ["2026-04-14", "interval", 4000, 116, 29, "4x1000m, better pacing"],
        ["2026-04-16", "test_piece", 2000, 119, 31, "practice 2k"],
    ]

    for workout in sample_workouts:
        add_workout(
            workouts,
            workout[0],
            workout[1],
            workout[2],
            workout[3],
            workout[4],
            workout[5]
        )

    save_workouts(workouts)
    print("Sample data added.")


def show_menu():
    print("\nRowing Workout Tracker")
    print("=" * 30)
    print("1. Add workout")
    print("2. View workouts")
    print("3. Summary by workout type")
    print("4. Compare recent progress")
    print("5. Consistency score")
    print("6. Estimate 2k")
    print("7. Add sample data")
    print("8. Save and quit")


def main():
    workouts = load_workouts()

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_workout_from_user(workouts)

        elif choice == "2":
            display_workouts(workouts)

        elif choice == "3":
            summary_by_type(workouts)

        elif choice == "4":
            workout_type = choose_workout_type()
            if workout_type != "invalid":
                print(compare_recent_to_past(workouts, workout_type))

        elif choice == "5":
            workout_type = choose_workout_type()
            if workout_type != "invalid":
                score = consistency_score(workouts, workout_type)

                if score is None:
                    print("Need at least 2 workouts to calculate consistency.")
                else:
                    print(f"Consistency score: {score:.1f} seconds. Lower is better.")

        elif choice == "6":
            print("\n" + predict_2k(workouts))

        elif choice == "7":
            add_sample_data(workouts)

        elif choice == "8":
            save_workouts(workouts)
            print("Workouts saved. Goodbye!")
            break

        else:
            print("Invalid option. Choose 1-8.")


if __name__ == "__main__":
    main()
