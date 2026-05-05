# cs32-final-project
My CS32 Project with Kaelea Severino.
# Rowing Workout Tracker

## Project Description

This project is a rowing workout tracker designed to help rowers log workouts, analyze their training, and track progress toward improving their 2k performance.

Users can add workouts with information such as date, workout type, distance, average split, stroke rate, and notes. The program then uses this data to show workout history, summarize performance by workout type, compare recent workouts to earlier workouts, calculate consistency, and estimate a possible 2k split.

This project was created for our final project. Since our FP Status submission, we expanded the project from a basic command-line prototype into a full web application using Flask, JavaScript, and CSS that accepts real user input and persists workout data between runs.

## Features

- Add a new workout through a web interface
- View all logged workouts in a dynamic workout history table
- Save and load workouts using a JSON file for persistent storage
- Validate user input to prevent invalid dates, workout types, or incorrect formats
- Group workouts by type (steady state, interval, test piece, cross training)
- Calculate key performance metrics such as:
  - Average split
  - Average stroke rate
  - Total distance
  - Best split
- Compare the last 3 workouts to the previous 3 workouts to track progress over time
- Calculate a consistency score to measure variation in performance
- Estimate a 2k split using recent interval and test-piece workouts
- Display analytics and summaries by workout type
- Visualize performance trends using charts (e.g., split over time)
- Add sample data for testing and demonstration
## External Contributors and Use of AI

We used generative AI tools, specifically ChatGPT and Claude, throughout the development of this project.

We used AI as a coding assistant, design tool, and debugging resource, especially when expanding our project beyond the original scope.

AI helped us in the following ways:

- Brainstorming the overall structure of the project and how to organize it into separate components, including backend logic, Flask routes, frontend JavaScript, styling, and data storage.
- Assisting in the transition from our original command-line (menu-based) Python program to a more advanced web-based application using Flask.
- Helping write and refine JavaScript code for the frontend, including:
  - Tab navigation
  - Fetching data from backend API routes
  - Rendering workout history dynamically
  - Handling user input and form validation
  - Updating the dashboard and analytics in real time
- Helping design and implement the CSS styling for the website, including layout, dark theme, cards, navigation, and responsive elements.
- Assisting with connecting the frontend and backend using API endpoints such as `/api/workouts`, `/api/dashboard`, and `/api/summary`.
- Supporting development of backend Python features, including:
  - Input validation
  - JSON file storage and persistence
  - Data analysis functions such as summary statistics, consistency score, progress comparison, and 2k prediction
- Helping improve code readability, structure, and commenting.

Some portions of the JavaScript and CSS were generated with the help of AI tools and then reviewed, tested, and modified by us. We made sure we understood how the code worked and adapted it to fit our project goals.

Overall, AI allowed us to go beyond the original scope of the project by helping us build a full web application and implement more advanced data analysis features than we had previously learned in class.

## How to Run the Program

1. Make sure Python is installed on your computer.

2. Install required packages:

```
pip install -r requirements.txt
```

3. Run the Flask app:

```
python app.py
```

4. Open your browser and go to:

```
http://127.0.0.1:5000/
```

5. Use the interface (or API endpoints) to:

* Add workouts
* View workout history
* Analyze performance


