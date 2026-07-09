from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "student_timetable_ai_secret_key"

DATABASE = "student_timetable.db"


# -------------------------------
# DATABASE CONNECTION
# -------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# CREATE TABLES
# -------------------------------

def init_db():

    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # SUBJECTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject_name TEXT,
        difficulty TEXT,
        study_hours REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # TIMETABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        day TEXT,
        start_time TEXT,
        end_time TEXT,
        subject TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # ASSIGNMENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        subject TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # HOMEWORK
    cur.execute("""
    CREATE TABLE IF NOT EXISTS homework(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        subject TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # EXAMS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        exam_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # ATTENDANCE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        attended INTEGER DEFAULT 0,
        total INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# -------------------------------
# LOGIN REQUIRED
# -------------------------------

def login_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return wrapper


# -------------------------------
# HOME
# -------------------------------

@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# -------------------------------
# REGISTER
# -------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not name or not email or not password:
            return jsonify({"success": False, "message": "Please fill all fields."}), 400

        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match."}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        if cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "An account with this email already exists."}), 409

        hashed = generate_password_hash(password)

        cur.execute("""
        INSERT INTO users(name,email,password)
        VALUES(?,?,?)
        """, (name, email, hashed))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Registration Successful!"})

    return render_template("register.html")


# -------------------------------
# LOGIN
# -------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# -------------------------------
# LOGOUT
# -------------------------------

@app.route("/logout")
@login_required
def logout():

    session.clear()

    return redirect(url_for("login"))


# -------------------------------
# DASHBOARD
# -------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        username=session["user_name"]
    )


# -------------------------------
# API : USER INFO
# -------------------------------

@app.route("/api/user")
@login_required
def user_info():

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE id=?", (session["user_id"],))
    row = cur.fetchone()
    conn.close()

    return jsonify({
        "id": session["user_id"],
        "name": session["user_name"],
        "email": row["email"] if row else ""
    })


# -------------------------------
# START APP
# -------------------------------

# ============================================
# SUBJECT MANAGEMENT
# ============================================

@app.route("/api/subjects", methods=["GET", "POST"])
@login_required
def subjects():

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        data = request.get_json()

        subject = data.get("subject")
        difficulty = data.get("difficulty")
        hours = data.get("hours")

        if not subject:
            return jsonify({"success": False, "message": "Subject required"}), 400

        cur.execute("""
        INSERT INTO subjects(user_id,subject_name,difficulty,study_hours)
        VALUES(?,?,?,?)
        """, (
            session["user_id"],
            subject,
            difficulty,
            hours
        ))

        conn.commit()

        conn.close()

        return jsonify({
            "success": True,
            "message": "Subject Added"
        })

    cur.execute("""
    SELECT *
    FROM subjects
    WHERE user_id=?
    """, (session["user_id"],))

    rows = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(rows)


# ============================================
# DELETE SUBJECT
# ============================================

@app.route("/api/subjects/<int:id>", methods=["DELETE"])
@login_required
def delete_subject(id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    DELETE FROM subjects
    WHERE id=?
    AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True
    })


# ============================================
# SMART TIMETABLE GENERATOR
# ============================================

def generate_timetable(user_id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM subjects
    WHERE user_id=?
    """, (user_id,))

    subjects = cur.fetchall()

    cur.execute("""
    DELETE FROM timetable
    WHERE user_id=?
    """, (user_id,))

    conn.commit()

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]

    current_day = 0

    start_hour = 17

    for subject in subjects:

        hrs = subject["study_hours"] or 1

        if subject["difficulty"] == "Hard":
            hrs += 1

        if hrs > 3:
            hrs = 3

        start = start_hour
        end = start + hrs

        cur.execute("""
        INSERT INTO timetable(
        user_id,
        day,
        start_time,
        end_time,
        subject
        )
        VALUES(?,?,?,?,?)
        """, (
            user_id,
            days[current_day],
            f"{start}:00",
            f"{end}:00",
            subject["subject_name"]
        ))

        current_day += 1

        if current_day >= len(days):
            current_day = 0

    conn.commit()

    conn.close()


# ============================================
# GENERATE TIMETABLE
# ============================================

@app.route("/api/timetable/generate", methods=["POST"])
@login_required
def create_timetable():

    generate_timetable(session["user_id"])

    return jsonify({
        "success": True,
        "message": "Timetable Generated Successfully"
    })


# ============================================
# VIEW TIMETABLE
# ============================================

@app.route("/api/timetable")
@login_required
def timetable():

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM timetable
    WHERE user_id=?
    ORDER BY
    day,
    start_time
    """, (session["user_id"],))

    data = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(data)


# ============================================
# DELETE TIMETABLE
# ============================================

@app.route("/api/timetable", methods=["DELETE"])
@login_required
def delete_timetable():

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    DELETE FROM timetable
    WHERE user_id=?
    """, (session["user_id"],))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True
    })


# ============================================
# DASHBOARD API
# ============================================

@app.route("/api/dashboard")
@login_required
def dashboard_api():

    conn = get_db()

    cur = conn.cursor()

    user = session["user_id"]

    cur.execute("SELECT COUNT(*) FROM assignments WHERE user_id=?", (user,))
    assignments = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM homework WHERE user_id=?", (user,))
    homework = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM exams WHERE user_id=?", (user,))
    exams = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM timetable WHERE user_id=?", (user,))
    timetable = cur.fetchone()[0]

    cur.execute("""
    SELECT attended,total
    FROM attendance
    WHERE user_id=?
    """, (user,))

    row = cur.fetchone()

    attendance = 0

    if row:

        if row["total"] > 0:

            attendance = round(
                row["attended"] /
                row["total"] * 100,
                2
            )

    conn.close()

    return jsonify({

        "assignments": assignments,
        "homework": homework,
        "exams": exams,
        "timetable": timetable,
        "attendance": attendance,
        "username": session["user_name"]

    })
# ============================================
# ASSIGNMENTS
# ============================================

@app.route("/api/assignments", methods=["GET", "POST"])
@login_required
def assignments():

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        data = request.get_json()

        title = data.get("title")
        subject = data.get("subject")
        due_date = data.get("due_date")

        if not title or not subject or not due_date:
            return jsonify({
                "success": False,
                "message": "Please fill all fields."
            }), 400

        cur.execute("""
        INSERT INTO assignments
        (user_id,title,subject,due_date,status)
        VALUES(?,?,?,?,?)
        """, (
            session["user_id"],
            title,
            subject,
            due_date,
            "Pending"
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Assignment Added"
        })

    cur.execute("""
    SELECT *
    FROM assignments
    WHERE user_id=?
    ORDER BY due_date ASC
    """, (session["user_id"],))

    assignments = []

    today = datetime.now().date()

    for row in cur.fetchall():

        item = dict(row)

        try:
            due = datetime.strptime(
                item["due_date"],
                "%Y-%m-%d"
            ).date()

            item["days_left"] = (due - today).days
            item["overdue"] = due < today

        except:
            item["days_left"] = None
            item["overdue"] = False

        assignments.append(item)

    conn.close()

    return jsonify(assignments)


# ============================================
# UPDATE ASSIGNMENT
# ============================================

@app.route("/api/assignments/<int:id>", methods=["PUT"])
@login_required
def update_assignment(id):

    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE assignments
    SET
    title=?,
    subject=?,
    due_date=?,
    status=?
    WHERE id=?
    AND user_id=?
    """, (

        data.get("title"),
        data.get("subject"),
        data.get("due_date"),
        data.get("status"),
        id,
        session["user_id"]

    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ============================================
# DELETE ASSIGNMENT
# ============================================

@app.route("/api/assignments/<int:id>", methods=["DELETE"])
@login_required
def delete_assignment(id):

    conn = get_db()

    conn.execute("""
    DELETE FROM assignments
    WHERE id=?
    AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ============================================
# HOMEWORK
# ============================================

@app.route("/api/homework", methods=["GET", "POST"])
@login_required
def homework():

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        data = request.get_json()

        cur.execute("""
        INSERT INTO homework
        (user_id,title,subject,due_date,status)
        VALUES(?,?,?,?,?)
        """, (

            session["user_id"],
            data.get("title"),
            data.get("subject"),
            data.get("due_date"),
            "Pending"

        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Homework Added"
        })

    cur.execute("""
    SELECT *
    FROM homework
    WHERE user_id=?
    ORDER BY due_date ASC
    """, (session["user_id"],))

    homework = []

    today = datetime.now().date()

    for row in cur.fetchall():

        item = dict(row)

        try:
            due = datetime.strptime(
                item["due_date"],
                "%Y-%m-%d"
            ).date()

            item["days_left"] = (due - today).days
            item["overdue"] = due < today

        except:
            item["days_left"] = None
            item["overdue"] = False

        homework.append(item)

    conn.close()

    return jsonify(homework)


# ============================================
# UPDATE HOMEWORK
# ============================================

@app.route("/api/homework/<int:id>", methods=["PUT"])
@login_required
def update_homework(id):

    data = request.get_json()

    conn = get_db()

    conn.execute("""
    UPDATE homework
    SET
    title=?,
    subject=?,
    due_date=?,
    status=?
    WHERE id=?
    AND user_id=?
    """, (

        data.get("title"),
        data.get("subject"),
        data.get("due_date"),
        data.get("status"),
        id,
        session["user_id"]

    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ============================================
# DELETE HOMEWORK
# ============================================

@app.route("/api/homework/<int:id>", methods=["DELETE"])
@login_required
def delete_homework(id):

    conn = get_db()

    conn.execute("""
    DELETE FROM homework
    WHERE id=?
    AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})
# ============================================
# EXAM MANAGER
# ============================================

@app.route("/api/exams", methods=["GET", "POST"])
@login_required
def exams():

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        data = request.get_json()

        subject = data.get("subject")
        exam_date = data.get("exam_date")

        if not subject or not exam_date:
            return jsonify({
                "success": False,
                "message": "Please fill all fields."
            }), 400

        cur.execute("""
        INSERT INTO exams(user_id,subject,exam_date)
        VALUES(?,?,?)
        """, (
            session["user_id"],
            subject,
            exam_date
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Exam Added"
        })

    cur.execute("""
    SELECT *
    FROM exams
    WHERE user_id=?
    ORDER BY exam_date ASC
    """, (session["user_id"],))

    exams = []

    today = datetime.now().date()

    for row in cur.fetchall():

        exam = dict(row)

        try:
            date = datetime.strptime(
                exam["exam_date"],
                "%Y-%m-%d"
            ).date()

            exam["days_left"] = (date - today).days

            exam["status"] = (
                "Upcoming"
                if date >= today
                else "Completed"
            )

        except:
            exam["days_left"] = None
            exam["status"] = "Unknown"

        exams.append(exam)

    conn.close()

    return jsonify(exams)


# ============================================
# UPDATE EXAM
# ============================================

@app.route("/api/exams/<int:id>", methods=["PUT"])
@login_required
def update_exam(id):

    data = request.get_json()

    conn = get_db()

    conn.execute("""
    UPDATE exams
    SET subject=?,
        exam_date=?
    WHERE id=?
    AND user_id=?
    """, (

        data.get("subject"),
        data.get("exam_date"),
        id,
        session["user_id"]

    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ============================================
# DELETE EXAM
# ============================================

@app.route("/api/exams/<int:id>", methods=["DELETE"])
@login_required
def delete_exam(id):

    conn = get_db()

    conn.execute("""
    DELETE FROM exams
    WHERE id=?
    AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ============================================
# ATTENDANCE
# ============================================

@app.route("/api/attendance", methods=["GET", "POST"])
@login_required
def attendance():

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        data = request.get_json()

        attended = int(data.get("attended", 0))
        total = int(data.get("total", 0))

        cur.execute("""
        SELECT id
        FROM attendance
        WHERE user_id=?
        """, (session["user_id"],))

        row = cur.fetchone()

        if row:

            cur.execute("""
            UPDATE attendance
            SET attended=?,
                total=?
            WHERE user_id=?
            """, (

                attended,
                total,
                session["user_id"]

            ))

        else:

            cur.execute("""
            INSERT INTO attendance(
            user_id,
            attended,
            total
            )
            VALUES(?,?,?)
            """, (

                session["user_id"],
                attended,
                total

            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Attendance Saved"
        })

    cur.execute("""
    SELECT attended,total
    FROM attendance
    WHERE user_id=?
    """, (session["user_id"],))

    row = cur.fetchone()

    conn.close()

    if not row:

        return jsonify({
            "attended": 0,
            "total": 0,
            "percentage": 0,
            "need": 0,
            "status": "No Data"
        })

    attended = row["attended"]
    total = row["total"]

    percentage = 0

    if total > 0:
        percentage = round(attended / total * 100, 2)

    need = 0

    if percentage < 75:

        while True:

            attended += 1
            total += 1
            need += 1

            if attended / total >= 0.75:
                break

    return jsonify({

        "attended": row["attended"],
        "total": row["total"],
        "percentage": percentage,
        "need": need,
        "status":
            "Good"
            if percentage >= 75
            else "Below 75%"

    })


# ============================================
# DASHBOARD SUMMARY
# ============================================

@app.route("/api/dashboard/summary")
@login_required
def dashboard_summary():

    conn = get_db()
    cur = conn.cursor()

    uid = session["user_id"]

    tables = [
        "subjects",
        "assignments",
        "homework",
        "exams",
        "timetable"
    ]

    data = {}

    for table in tables:

        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE user_id=?",
            (uid,)
        )

        data[table] = cur.fetchone()[0]

    cur.execute("""
    SELECT attended,total
    FROM attendance
    WHERE user_id=?
    """, (uid,))

    row = cur.fetchone()

    if row and row["total"] > 0:

        attendance = round(
            row["attended"] /
            row["total"] * 100,
            2
        )

    else:
        attendance = 0

    conn.close()

    data["attendance"] = attendance
    data["username"] = session["user_name"]

    return jsonify(data)
# ============================================
# UPDATE SUBJECT
# ============================================

@app.route("/api/subjects/<int:id>", methods=["PUT"])
@login_required
def update_subject(id):

    data = request.get_json()

    conn = get_db()

    conn.execute("""
    UPDATE subjects
    SET
        subject_name=?,
        difficulty=?,
        study_hours=?
    WHERE id=?
    AND user_id=?
    """, (
        data.get("subject"),
        data.get("difficulty"),
        data.get("hours"),
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Subject Updated"
    })


# ============================================
# SEARCH SUBJECTS
# ============================================

@app.route("/api/subjects/search")
@login_required
def search_subjects():

    keyword = request.args.get("q", "")

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM subjects
    WHERE user_id=?
    AND subject_name LIKE ?
    """, (
        session["user_id"],
        f"%{keyword}%"
    ))

    rows = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(rows)


# ============================================
# TODAY'S TIMETABLE
# ============================================

@app.route("/api/timetable/today")
@login_required
def today_timetable():

    today = datetime.now().strftime("%A")

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM timetable
    WHERE user_id=?
    AND day=?
    ORDER BY start_time
    """, (
        session["user_id"],
        today
    ))

    timetable = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(timetable)


# ============================================
# UPCOMING EXAMS
# ============================================

@app.route("/api/exams/upcoming")
@login_required
def upcoming_exams():

    conn = get_db()

    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
    SELECT *
    FROM exams
    WHERE user_id=?
    AND exam_date>=?
    ORDER BY exam_date
    LIMIT 5
    """, (
        session["user_id"],
        today
    ))

    exams = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(exams)


# ============================================
# PENDING ASSIGNMENTS
# ============================================

@app.route("/api/assignments/pending")
@login_required
def pending_assignments():

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM assignments
    WHERE user_id=?
    AND status='Pending'
    ORDER BY due_date
    LIMIT 5
    """, (session["user_id"],))

    assignments = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(assignments)


# ============================================
# PENDING HOMEWORK
# ============================================

@app.route("/api/homework/pending")
@login_required
def pending_homework():

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM homework
    WHERE user_id=?
    AND status='Pending'
    ORDER BY due_date
    LIMIT 5
    """, (session["user_id"],))

    homework = [dict(x) for x in cur.fetchall()]

    conn.close()

    return jsonify(homework)


# ============================================
# HEALTH CHECK
# ============================================

@app.route("/api/status")
def status():

    return jsonify({

        "status": "online",
        "application": "Student Timetable AI",
        "version": "2.0"

    })


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "Page Not Found"
    }), 404


@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "success": False,
        "message": "Internal Server Error"
    }), 500


# ============================================
# START APP
# ============================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )