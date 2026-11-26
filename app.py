from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-deployment"
DB_PATH = Path(__file__).with_name("student_tracker.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            class_name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            marks REAL NOT NULL CHECK(marks >= 0),
            max_marks REAL NOT NULL CHECK(max_marks > 0),
            exam_date TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
            UNIQUE(student_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        );
        """)
        if not db.execute("SELECT id FROM users WHERE username='admin'").fetchone():
            db.execute("INSERT INTO users(username,password_hash) VALUES(?,?)",
                       ("admin", generate_password_hash("admin123")))
        if db.execute("SELECT COUNT(*) AS n FROM students").fetchone()["n"] == 0:
            db.executemany(
                "INSERT INTO students(roll_no,name,email,class_name) VALUES(?,?,?,?)",
                [
                    ("STU001", "Aarav Sharma", "aarav@example.com", "BCA - 1"),
                    ("STU002", "Ananya Verma", "ananya@example.com", "BCA - 1"),
                    ("STU003", "Rohan Gupta", "rohan@example.com", "BCA - 2"),
                ],
            )
            rows = db.execute("SELECT id FROM students ORDER BY id").fetchall()
            today = date.today().isoformat()
            sample = [
                (rows[0]["id"], "Python", 86, 100, today),
                (rows[0]["id"], "DBMS", 78, 100, today),
                (rows[1]["id"], "Python", 92, 100, today),
                (rows[1]["id"], "DBMS", 88, 100, today),
                (rows[2]["id"], "Python", 69, 100, today),
            ]
            db.executemany(
                "INSERT INTO marks(student_id,subject,marks,max_marks,exam_date) VALUES(?,?,?,?,?)",
                sample
            )
            db.executemany(
                "INSERT INTO attendance(student_id,attendance_date,status) VALUES(?,?,?)",
                [(r["id"], today, "Present") for r in rows]
            )

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def grade(percent):
    if percent >= 90: return "A+"
    if percent >= 80: return "A"
    if percent >= 70: return "B"
    if percent >= 60: return "C"
    if percent >= 50: return "D"
    return "Needs Improvement"

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) n FROM students").fetchone()["n"]
        marks_count = db.execute("SELECT COUNT(*) n FROM marks").fetchone()["n"]
        avg = db.execute("SELECT AVG(100.0*marks/max_marks) a FROM marks").fetchone()["a"] or 0
        present = db.execute("SELECT COUNT(*) n FROM attendance WHERE status='Present'").fetchone()["n"]
        attendance_total = db.execute("SELECT COUNT(*) n FROM attendance").fetchone()["n"]
        attendance_rate = (100 * present / attendance_total) if attendance_total else 0
        students = db.execute("""
            SELECT s.*,
            COALESCE(ROUND(AVG(100.0*m.marks/m.max_marks),1),0) AS percentage
            FROM students s LEFT JOIN marks m ON s.id=m.student_id
            GROUP BY s.id ORDER BY percentage DESC, s.name
        """).fetchall()
        subject_rows = db.execute("""
            SELECT subject, ROUND(AVG(100.0*marks/max_marks),1) AS avg
            FROM marks GROUP BY subject ORDER BY subject
        """).fetchall()
    return render_template("dashboard.html", total=total, marks_count=marks_count,
                           avg=round(avg,1), attendance_rate=round(attendance_rate,1),
                           students=students, subject_rows=subject_rows)

@app.route("/students")
@login_required
def students():
    q = request.args.get("q", "").strip()
    with get_db() as db:
        rows = db.execute("""
            SELECT s.*, COALESCE(ROUND(AVG(100.0*m.marks/m.max_marks),1),0) percentage
            FROM students s LEFT JOIN marks m ON s.id=m.student_id
            WHERE s.name LIKE ? OR s.roll_no LIKE ? OR s.class_name LIKE ?
            GROUP BY s.id ORDER BY s.name
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return render_template("students.html", students=rows, q=q)

@app.route("/students/add", methods=["GET", "POST"])
@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def student_form(student_id=None):
    with get_db() as db:
        student = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone() if student_id else None
        if student_id and not student:
            flash("Student not found.", "error")
            return redirect(url_for("students"))
        if request.method == "POST":
            roll = request.form.get("roll_no", "").strip()
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            class_name = request.form.get("class_name", "").strip()
            if not roll or not name or not class_name:
                flash("Roll number, name and class are required.", "error")
            else:
                try:
                    if student_id:
                        db.execute("UPDATE students SET roll_no=?,name=?,email=?,class_name=? WHERE id=?",
                                   (roll, name, email, class_name, student_id))
                    else:
                        db.execute("INSERT INTO students(roll_no,name,email,class_name) VALUES(?,?,?,?)",
                                   (roll, name, email, class_name))
                    db.commit()
                    flash("Student saved successfully.", "success")
                    return redirect(url_for("students"))
                except sqlite3.IntegrityError:
                    flash("That roll number is already in use.", "error")
        return render_template("student_form.html", student=student)

@app.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id=?", (student_id,))
    flash("Student and related records deleted.", "success")
    return redirect(url_for("students"))

@app.route("/students/<int:student_id>")
@login_required
def student_detail(student_id):
    with get_db() as db:
        student = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        if not student:
            flash("Student not found.", "error")
            return redirect(url_for("students"))
        marks = db.execute("SELECT * FROM marks WHERE student_id=? ORDER BY exam_date DESC,id DESC",
                           (student_id,)).fetchall()
        attendance = db.execute("""
            SELECT COUNT(*) total, SUM(status='Present') present
            FROM attendance WHERE student_id=?
        """, (student_id,)).fetchone()
    total = attendance["total"] or 0
    present = attendance["present"] or 0
    attendance_rate = round(100*present/total, 1) if total else 0
    percentages = [100*m["marks"]/m["max_marks"] for m in marks]
    average = round(sum(percentages)/len(percentages), 1) if percentages else 0
    return render_template("student_detail.html", student=student, marks=marks,
                           average=average, grade=grade(average),
                           attendance_rate=attendance_rate, attendance_total=total)

@app.route("/marks", methods=["GET", "POST"])
@login_required
def marks():
    with get_db() as db:
        if request.method == "POST":
            try:
                student_id = int(request.form["student_id"])
                subject = request.form["subject"].strip()
                score = float(request.form["marks"])
                maximum = float(request.form["max_marks"])
                exam_date = request.form["exam_date"]
                if not subject or maximum <= 0 or score < 0 or score > maximum:
                    raise ValueError()
                db.execute("""INSERT INTO marks(student_id,subject,marks,max_marks,exam_date)
                              VALUES(?,?,?,?,?)""",
                           (student_id, subject, score, maximum, exam_date))
                db.commit()
                flash("Marks added successfully.", "success")
                return redirect(url_for("marks"))
            except (ValueError, KeyError, sqlite3.IntegrityError):
                flash("Please enter valid marks and student details.", "error")
        students = db.execute("SELECT id,roll_no,name FROM students ORDER BY name").fetchall()
        records = db.execute("""
            SELECT m.*,s.name,s.roll_no FROM marks m
            JOIN students s ON s.id=m.student_id ORDER BY m.exam_date DESC,m.id DESC
        """).fetchall()
    return render_template("marks.html", students=students, records=records,
                           today=date.today().isoformat())

@app.route("/marks/<int:mark_id>/delete", methods=["POST"])
@login_required
def delete_mark(mark_id):
    with get_db() as db:
        db.execute("DELETE FROM marks WHERE id=?", (mark_id,))
    flash("Mark record deleted.", "success")
    return redirect(url_for("marks"))

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    with get_db() as db:
        if request.method == "POST":
            try:
                student_id = int(request.form["student_id"])
                attendance_date = request.form["attendance_date"]
                status = request.form["status"]
                if status not in ("Present", "Absent"):
                    raise ValueError()
                db.execute("""
                    INSERT INTO attendance(student_id,attendance_date,status) VALUES(?,?,?)
                    ON CONFLICT(student_id,attendance_date) DO UPDATE SET status=excluded.status
                """, (student_id, attendance_date, status))
                db.commit()
                flash("Attendance saved.", "success")
                return redirect(url_for("attendance"))
            except (ValueError, KeyError, sqlite3.IntegrityError):
                flash("Please enter valid attendance details.", "error")
        students = db.execute("SELECT id,roll_no,name FROM students ORDER BY name").fetchall()
        records = db.execute("""
            SELECT a.*,s.name,s.roll_no FROM attendance a
            JOIN students s ON s.id=a.student_id
            ORDER BY a.attendance_date DESC,s.name LIMIT 100
        """).fetchall()
    return render_template("attendance.html", students=students, records=records,
                           today=date.today().isoformat())

@app.route("/reports")
@login_required
def reports():
    with get_db() as db:
        rows = db.execute("""
            SELECT s.roll_no,s.name,s.class_name,
            COALESCE(ROUND(AVG(100.0*m.marks/m.max_marks),1),0) percentage,
            COUNT(m.id) exams
            FROM students s LEFT JOIN marks m ON s.id=m.student_id
            GROUP BY s.id ORDER BY percentage DESC
        """).fetchall()
    return render_template("reports.html", students=rows, grade=grade)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
