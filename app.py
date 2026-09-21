from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import re

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "student_timetable_ai_secret_key")

# Render PostgreSQL provides DATABASE_URL automatically when the database is linked.
# Local development can also use DATABASE_URL from a .env/environment variable.
def get_database_url():
    """Return a normalized PostgreSQL connection URL."""
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Please configure the DATABASE_URL "
            "environment variable."
        )

    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]

    return database_url 


def get_db():
    """Open a PostgreSQL connection and return it with dictionary-like rows."""
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed. Add psycopg2-binary to requirements.txt.")

    return psycopg2.connect(
        get_database_url(),
        cursor_factory=RealDictCursor,
        sslmode=os.environ.get("PGSSLMODE", "require")
    )


def query_one(sql, params=()):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()


def query_all(sql, params=()):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=(), fetchone=False):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchone() if fetchone else None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -------------------------------
# CREATE TABLES
# -------------------------------
def init_db():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    subject_name TEXT,
                    difficulty TEXT,
                    study_hours DOUBLE PRECISION
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS timetable (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    day TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    subject TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT,
                    subject TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'Pending'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS homework (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT,
                    subject TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'Pending'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    subject TEXT,
                    exam_date TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    attended INTEGER DEFAULT 0,
                    total INTEGER DEFAULT 0
                )
            """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
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


def clean_email(email):
    return (email or "").strip().lower()


def date_info(value):
    today = datetime.now().date()
    try:
        due = datetime.strptime(value, "%Y-%m-%d").date()
        return (due - today).days, due < today
    except (TypeError, ValueError):
        return None, False


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
        name = (request.form.get("name") or "").strip()
        email = clean_email(request.form.get("email"))
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not name or not email or not password:
            return jsonify({"success": False, "message": "Please fill all fields."}), 400
        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match."}), 400
        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

        existing = query_one("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        if existing:
            return jsonify({"success": False, "message": "An account with this email already exists."}), 409

        hashed = generate_password_hash(password)
        try:
            execute(
                "INSERT INTO users(name, email, password) VALUES(%s, %s, %s)",
                (name, email, hashed)
            )
        except psycopg2.errors.UniqueViolation:
            return jsonify({"success": False, "message": "An account with this email already exists."}), 409

        return jsonify({"success": True, "message": "Registration Successful!"})

    return render_template("register.html")


# -------------------------------
# LOGIN
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = clean_email(request.form.get("email"))
        password = request.form.get("password") or ""

        user = query_one("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,))

        if user and check_password_hash(user["password"], password):
            session.clear()
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
    return render_template("dashboard.html", username=session["user_name"])


# -------------------------------
# USER INFO
# -------------------------------
@app.route("/api/user")
@login_required
def user_info():
    row = query_one("SELECT email FROM users WHERE id=%s", (session["user_id"],))
    return jsonify({
        "id": session["user_id"],
        "name": session["user_name"],
        "email": row["email"] if row else ""
    })


# ============================================
# SUBJECT MANAGEMENT
# ============================================
@app.route("/api/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    uid = session["user_id"]

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        subject = (data.get("subject") or "").strip()
        difficulty = data.get("difficulty")
        hours = data.get("hours")

        if not subject:
            return jsonify({"success": False, "message": "Subject required"}), 400

        execute(
            "INSERT INTO subjects(user_id, subject_name, difficulty, study_hours) VALUES(%s, %s, %s, %s)",
            (uid, subject, difficulty, hours)
        )
        return jsonify({"success": True, "message": "Subject Added"})

    rows = query_all("SELECT * FROM subjects WHERE user_id=%s ORDER BY id", (uid,))
    return jsonify([dict(x) for x in rows])


@app.route("/api/subjects/<int:id>", methods=["PUT", "DELETE"])
@login_required
def subject_by_id(id):
    uid = session["user_id"]

    if request.method == "DELETE":
        execute("DELETE FROM subjects WHERE id=%s AND user_id=%s", (id, uid))
        return jsonify({"success": True})

    data = request.get_json(silent=True) or {}
    execute("""
        UPDATE subjects
        SET subject_name=%s, difficulty=%s, study_hours=%s
        WHERE id=%s AND user_id=%s
    """, (data.get("subject"), data.get("difficulty"), data.get("hours"), id, uid))
    return jsonify({"success": True, "message": "Subject Updated"})


@app.route("/api/subjects/search")
@login_required
def search_subjects():
    keyword = request.args.get("q", "")
    rows = query_all("""
        SELECT * FROM subjects
        WHERE user_id=%s AND subject_name ILIKE %s
        ORDER BY id
    """, (session["user_id"], f"%{keyword}%"))
    return jsonify([dict(x) for x in rows])


# ============================================
# SMART TIMETABLE
# ============================================
def generate_timetable(user_id):
    subjects_rows = query_all("SELECT * FROM subjects WHERE user_id=%s ORDER BY id", (user_id,))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM timetable WHERE user_id=%s", (user_id,))
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            current_day = 0
            start_hour = 17

            for subject in subjects_rows:
                try:
                    hrs = float(subject["study_hours"] or 1)
                except (TypeError, ValueError):
                    hrs = 1

                if subject["difficulty"] == "Hard":
                    hrs += 1
                hrs = min(hrs, 3)

                start = start_hour
                end = start + hrs
                start_text = f"{int(start):02d}:00"
                if float(end).is_integer():
                    end_text = f"{int(end):02d}:00"
                else:
                    end_text = f"{int(end):02d}:30"

                cur.execute("""
                    INSERT INTO timetable(user_id, day, start_time, end_time, subject)
                    VALUES(%s, %s, %s, %s, %s)
                """, (user_id, days[current_day], start_text, end_text, subject["subject_name"]))

                current_day = (current_day + 1) % len(days)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.route("/api/timetable/generate", methods=["POST"])
@login_required
def create_timetable():
    generate_timetable(session["user_id"])
    return jsonify({"success": True, "message": "Timetable Generated Successfully"})


@app.route("/api/timetable", methods=["GET", "DELETE"])
@login_required
def timetable():
    uid = session["user_id"]
    if request.method == "DELETE":
        execute("DELETE FROM timetable WHERE user_id=%s", (uid,))
        return jsonify({"success": True})

    rows = query_all("""
        SELECT * FROM timetable
        WHERE user_id=%s
        ORDER BY CASE day
            WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END,
            start_time
    """, (uid,))
    return jsonify([dict(x) for x in rows])


@app.route("/api/timetable/today")
@login_required
def today_timetable():
    rows = query_all("""
        SELECT * FROM timetable
        WHERE user_id=%s AND day=%s
        ORDER BY start_time
    """, (session["user_id"], datetime.now().strftime("%A")))
    return jsonify([dict(x) for x in rows])


# ============================================
# ASSIGNMENTS
# ============================================
@app.route("/api/assignments", methods=["GET", "POST"])
@login_required
def assignments():
    uid = session["user_id"]
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        title = data.get("title")
        subject = data.get("subject")
        due_date = data.get("due_date")
        if not title or not subject or not due_date:
            return jsonify({"success": False, "message": "Please fill all fields."}), 400
        execute("""
            INSERT INTO assignments(user_id,title,subject,due_date,status)
            VALUES(%s,%s,%s,%s,%s)
        """, (uid, title, subject, due_date, "Pending"))
        return jsonify({"success": True, "message": "Assignment Added"})

    rows = query_all("SELECT * FROM assignments WHERE user_id=%s ORDER BY due_date ASC", (uid,))
    result = []
    for row in rows:
        item = dict(row)
        item["days_left"], item["overdue"] = date_info(item.get("due_date"))
        result.append(item)
    return jsonify(result)


@app.route("/api/assignments/<int:id>", methods=["PUT", "DELETE"])
@login_required
def assignment_by_id(id):
    uid = session["user_id"]
    if request.method == "DELETE":
        execute("DELETE FROM assignments WHERE id=%s AND user_id=%s", (id, uid))
        return jsonify({"success": True})

    data = request.get_json(silent=True) or {}
    execute("""
        UPDATE assignments
        SET title=%s, subject=%s, due_date=%s, status=%s
        WHERE id=%s AND user_id=%s
    """, (data.get("title"), data.get("subject"), data.get("due_date"), data.get("status"), id, uid))
    return jsonify({"success": True})


@app.route("/api/assignments/pending")
@login_required
def pending_assignments():
    rows = query_all("""
        SELECT * FROM assignments
        WHERE user_id=%s AND status='Pending'
        ORDER BY due_date LIMIT 5
    """, (session["user_id"],))
    return jsonify([dict(x) for x in rows])


# ============================================
# HOMEWORK
# ============================================
@app.route("/api/homework", methods=["GET", "POST"])
@login_required
def homework():
    uid = session["user_id"]
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if not data.get("title") or not data.get("subject") or not data.get("due_date"):
            return jsonify({"success": False, "message": "Please fill all fields."}), 400
        execute("""
            INSERT INTO homework(user_id,title,subject,due_date,status)
            VALUES(%s,%s,%s,%s,%s)
        """, (uid, data.get("title"), data.get("subject"), data.get("due_date"), "Pending"))
        return jsonify({"success": True, "message": "Homework Added"})

    rows = query_all("SELECT * FROM homework WHERE user_id=%s ORDER BY due_date ASC", (uid,))
    result = []
    for row in rows:
        item = dict(row)
        item["days_left"], item["overdue"] = date_info(item.get("due_date"))
        result.append(item)
    return jsonify(result)


@app.route("/api/homework/<int:id>", methods=["PUT", "DELETE"])
@login_required
def homework_by_id(id):
    uid = session["user_id"]
    if request.method == "DELETE":
        execute("DELETE FROM homework WHERE id=%s AND user_id=%s", (id, uid))
        return jsonify({"success": True})

    data = request.get_json(silent=True) or {}
    execute("""
        UPDATE homework
        SET title=%s, subject=%s, due_date=%s, status=%s
        WHERE id=%s AND user_id=%s
    """, (data.get("title"), data.get("subject"), data.get("due_date"), data.get("status"), id, uid))
    return jsonify({"success": True})


@app.route("/api/homework/pending")
@login_required
def pending_homework():
    rows = query_all("""
        SELECT * FROM homework
        WHERE user_id=%s AND status='Pending'
        ORDER BY due_date LIMIT 5
    """, (session["user_id"],))
    return jsonify([dict(x) for x in rows])


# ============================================
# EXAMS
# ============================================
@app.route("/api/exams", methods=["GET", "POST"])
@login_required
def exams():
    uid = session["user_id"]
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if not data.get("subject") or not data.get("exam_date"):
            return jsonify({"success": False, "message": "Please fill all fields."}), 400
        execute("INSERT INTO exams(user_id,subject,exam_date) VALUES(%s,%s,%s)",
                (uid, data.get("subject"), data.get("exam_date")))
        return jsonify({"success": True, "message": "Exam Added"})

    rows = query_all("SELECT * FROM exams WHERE user_id=%s ORDER BY exam_date ASC", (uid,))
    result = []
    today = datetime.now().date()
    for row in rows:
        item = dict(row)
        try:
            d = datetime.strptime(item["exam_date"], "%Y-%m-%d").date()
            item["days_left"] = (d - today).days
            item["status"] = "Upcoming" if d >= today else "Completed"
        except (TypeError, ValueError):
            item["days_left"] = None
            item["status"] = "Unknown"
        result.append(item)
    return jsonify(result)


@app.route("/api/exams/<int:id>", methods=["PUT", "DELETE"])
@login_required
def exam_by_id(id):
    uid = session["user_id"]
    if request.method == "DELETE":
        execute("DELETE FROM exams WHERE id=%s AND user_id=%s", (id, uid))
        return jsonify({"success": True})

    data = request.get_json(silent=True) or {}
    execute("""
        UPDATE exams SET subject=%s, exam_date=%s
        WHERE id=%s AND user_id=%s
    """, (data.get("subject"), data.get("exam_date"), id, uid))
    return jsonify({"success": True})


@app.route("/api/exams/upcoming")
@login_required
def upcoming_exams():
    today = datetime.now().strftime("%Y-%m-%d")
    rows = query_all("""
        SELECT * FROM exams
        WHERE user_id=%s AND exam_date>=%s
        ORDER BY exam_date LIMIT 5
    """, (session["user_id"], today))
    return jsonify([dict(x) for x in rows])


# ============================================
# ATTENDANCE
# ============================================
@app.route("/api/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    uid = session["user_id"]

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        try:
            attended = max(0, int(data.get("attended", 0)))
            total = max(0, int(data.get("total", 0)))
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Attendance values must be numbers."}), 400

        if attended > total:
            return jsonify({"success": False, "message": "Attended classes cannot exceed total classes."}), 400

        execute("""
            INSERT INTO attendance(user_id, attended, total)
            VALUES(%s,%s,%s)
            ON CONFLICT (user_id)
            DO UPDATE SET attended=EXCLUDED.attended, total=EXCLUDED.total
        """, (uid, attended, total))
        return jsonify({"success": True, "message": "Attendance Saved"})

    row = query_one("SELECT attended,total FROM attendance WHERE user_id=%s", (uid,))
    if not row:
        return jsonify({"attended": 0, "total": 0, "percentage": 0, "need": 0, "status": "No Data"})

    attended = int(row["attended"] or 0)
    total = int(row["total"] or 0)
    percentage = round(attended / total * 100, 2) if total else 0

    need = 0
    if percentage < 75:
        # Minimum future classes needed to reach 75%.
        #  (attended + n) / (total + n) >= 0.75
        need = max(0, (3 * total - 4 * attended + 2) // 1)
        # Exact integer ceiling of (3*total - 4*attended) / 1 for 75%.
        if total:
            numerator = 3 * total - 4 * attended
            need = max(0, numerator)

    return jsonify({
        "attended": attended,
        "total": total,
        "percentage": percentage,
        "need": need,
        "status": "Good" if percentage >= 75 else "Below 75%"
    })


# ============================================
# DASHBOARD APIs
# ============================================
def attendance_percentage(uid):
    row = query_one("SELECT attended,total FROM attendance WHERE user_id=%s", (uid,))
    if not row or not row["total"]:
        return 0
    return round(row["attended"] / row["total"] * 100, 2)


@app.route("/api/dashboard")
@login_required
def dashboard_api():
    uid = session["user_id"]
    counts = {}
    for table in ["assignments", "homework", "exams", "timetable"]:
        row = query_one(f"SELECT COUNT(*) AS count FROM {table} WHERE user_id=%s", (uid,))
        counts[table] = int(row["count"])

    return jsonify({
        **counts,
        "attendance": attendance_percentage(uid),
        "username": session["user_name"]
    })


@app.route("/api/dashboard/summary")
@login_required
def dashboard_summary():
    uid = session["user_id"]
    data = {}
    for table in ["subjects", "assignments", "homework", "exams", "timetable"]:
        row = query_one(f"SELECT COUNT(*) AS count FROM {table} WHERE user_id=%s", (uid,))
        data[table] = int(row["count"])
    data["attendance"] = attendance_percentage(uid)
    data["username"] = session["user_name"]
    return jsonify(data)


# ============================================
# HEALTH CHECK
# ============================================
@app.route("/api/status")
def status():
    try:
        query_one("SELECT 1 AS ok")
        return jsonify({
            "status": "online",
            "database": "postgresql",
            "application": "Student Timetable AI",
            "version": "3.0"
        })
    except Exception as exc:
        return jsonify({
            "status": "online",
            "database": "error",
            "application": "Student Timetable AI",
            "version": "3.0",
            "error": str(exc) if app.debug else "Database connection failed"
        }), 503


# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Page Not Found"}), 404


@app.errorhandler(500)
def internal_error(error):
    # Keep the response JSON, but do not expose database credentials/details in production.
    return jsonify({"success": False, "message": "Internal Server Error"}), 500


# Initialize PostgreSQL when the Flask process starts.
# This is intentionally outside if __name__ == '__main__' so it also works with Gunicorn on Render.
try:
    init_db()
except Exception as startup_error:
    # Do not prevent Gunicorn from starting if PostgreSQL is temporarily unavailable.
    # The first database request will return an appropriate error instead.
    print(f"[DATABASE STARTUP WARNING] {startup_error}")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
