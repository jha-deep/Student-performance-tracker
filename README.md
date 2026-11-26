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
