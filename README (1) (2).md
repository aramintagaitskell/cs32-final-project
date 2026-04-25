# cs32-final-project
My CS32 Project with Kaelea Severino.
# Rowing Workout Tracker

## Project Description

This project is a rowing workout tracker designed to help rowers log workouts, analyze their training, and track progress toward improving their 2k performance.

Users can add workouts with information such as date, workout type, distance, average split, stroke rate, and notes. The program then uses this data to show workout history, summarize performance by workout type, compare recent workouts to earlier workouts, calculate consistency, and estimate a possible 2k split.

This project was created for our final project. Since our FP Design submission, we expanded the project from a basic prototype using sample data into a more interactive program that accepts real user input and saves workout data between runs.

## Features

- Add a new workout through a menu system
- View all logged workouts
- Save and load workouts using a JSON file
- Validate user input to avoid invalid dates, workout types, or negative values
- Group workouts by type
- Calculate average split, average stroke rate, total distance, and best split
- Compare the last 3 workouts to the previous 3 workouts
- Calculate a consistency score
- Estimate a 2k split using recent interval and test-piece workouts
- Add sample data for testing and demonstration

## External Contributors and Use of AI

We used concepts learned in class, including lists, dictionaries, functions, loops, conditionals, and input validation.

We also used ChatGPT to assist with brainstorming features, improving code organization, and refining parts of our implementation. Specifically, ChatGPT helped with:

- Designing the menu-based interface for user interaction (`show_menu` and `main` functions)
- Implementing file saving and loading using JSON (`save_workouts` and `load_workouts`)
- Suggesting improvements to data validation (such as checking date format, split format, and invalid inputs in `add_workout` and `add_workout_from_user`)
- Structuring analysis functions such as:
  - `summary_by_type` (grouping workouts and calculating statistics)
  - `compare_recent_to_past` (tracking improvement over time)
  - `consistency_score` (measuring variation in splits)
  - `predict_2k` (estimating 2k performance based on recent workouts)
- Adding comments and improving readability and organization of the code

All code generated with the help of ChatGPT was reviewed, modified, and integrated by us to ensure we understood how it works and that it fits our project goals.

## How to Run the Program

1. Make sure Python is installed on your computer.
2. Download or clone this repository.
3. Open the project folder in a local IDE, terminal, or code editor.
4. Run the Python file:


