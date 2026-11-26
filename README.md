# Student Performance Tracker

A beginner-friendly full-stack web application to manage students, exam marks, attendance, and academic performance reports.

## Features

- Admin login
- Student CRUD (create, read, update, delete)
- Search students by name, roll number, or class
- Add and delete assessment marks
- Record daily attendance (same student/date updates the existing record)
- Dashboard with summary cards and subject-wise chart
- Student profile with average score and attendance percentage
- Ranked performance report with grade labels
- SQLite database initialized automatically with sample records

## Tech stack

- Python 3
- Flask
- SQLite
- HTML, CSS
- Chart.js

## Run locally

1. Install Python 3.10 or newer.
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Create and activate a virtual environment:

   **Windows**
   ```bash
   py -m venv venv
   venv\Scripts\activate
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Start the app:
   ```bash
   python app.py
   ```
7. Open http://127.0.0.1:5000 in your browser.

## Demo credentials

- Username: `admin`
- Password: `admin123`

Change the demo password and Flask secret key before deploying this application publicly.

## GitHub upload

Create a new empty repository on GitHub, then run these commands from this folder:

```bash
git init
git add .
git commit -m "Initial commit: Student Performance Tracker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/student-performance-tracker.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

## Project structure

```text
student-performance-tracker/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html
│   ├── student_form.html
│   ├── student_detail.html
│   ├── marks.html
│   ├── attendance.html
│   └── reports.html
└── static/
    └── style.css
```

## Notes

This is an educational starter project. It uses a demo admin account and a development server. Before production use, add stronger account management, CSRF protection, secure secret management, backups, and deployment configuration.
