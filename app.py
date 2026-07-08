from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# APP CONFIGURATION
# ==========================================

app = Flask(__name__)
CORS(app)

DATABASE = "timetable_ai.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Homework
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS homework(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        title TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    # Assignments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        title TEXT,
        submission_date TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    # Exams
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        exam_date TEXT
    )
    """)

    # Attendance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        classes_attended INTEGER DEFAULT 0,
        total_classes INTEGER DEFAULT 0
    )
    """)

    # Timetable
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        day TEXT,
        subject TEXT,
        start_time TEXT,
        end_time TEXT
    )
    """)

    conn.commit()
    conn.close()


# ==========================================
# HTML ROUTES
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login-page")
def login_page():
    return render_template("login.html")


@app.route("/register-page")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ==========================================
# USER AUTHENTICATION HELPER
# ==========================================

def get_authenticated_user_id():

    user_id = request.headers.get("X-User-Id")

    if not user_id:
        return None

    try:
        return int(user_id)
    except:
        return None


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username == "" or password == "":
        return jsonify({"error": "Username and Password required"}), 400

    hashed = generate_password_hash(password)

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, hashed)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Registration Successful"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "error": "Username already exists"
        }), 400


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:

        return jsonify({
            "success": False,
            "error": "User not found"
        }), 404

    if not check_password_hash(user["password"], password):

        return jsonify({
            "success": False,
            "error": "Wrong password"
        }), 401

    return jsonify({

        "success": True,
        "message": "Login Successful",
        "user_id": user["id"],
        "username": user["username"]

    }), 200
# ==========================================
# CRUD HELPER
# ==========================================

def handle_crud(table_name, required_fields, optional_fields=None):

    user_id = get_authenticated_user_id()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # ---------------- GET ----------------

    if request.method == "GET":

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT * FROM {table_name} WHERE user_id=?",
            (user_id,)
        )

        data = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify(data), 200

    # ---------------- POST ----------------

    if request.method == "POST":

        data = request.get_json()

        for field in required_fields:

            if field not in data:

                return jsonify({
                    "error": f"{field} is required"
                }), 400

        fields = ["user_id"] + required_fields

        if optional_fields:
            fields += optional_fields

        values = [user_id]

        for field in required_fields:
            values.append(data.get(field))

        if optional_fields:
            for field in optional_fields:
                values.append(data.get(field))

        placeholders = ",".join(["?"] * len(values))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"""
            INSERT INTO {table_name}
            ({",".join(fields)})
            VALUES
            ({placeholders})
            """,
            values
        )

        conn.commit()

        new_id = cursor.lastrowid

        conn.close()

        return jsonify({
            "success": True,
            "id": new_id
        }), 201


# ==========================================
# SINGLE RECORD HELPER
# ==========================================

def handle_single_item(table_name, item_id):

    user_id = get_authenticated_user_id()

    if not user_id:
        return jsonify({"error":"Unauthorized"}),401


    # DELETE

    if request.method=="DELETE":

        conn=get_db_connection()

        cursor=conn.cursor()

        cursor.execute(

            f"DELETE FROM {table_name} WHERE id=? AND user_id=?",

            (item_id,user_id)

        )

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Deleted Successfully"

        })


    # UPDATE STATUS

    if request.method=="PUT":

        data=request.get_json()

        status=data.get("status")

        conn=get_db_connection()

        cursor=conn.cursor()

        cursor.execute(

            f"""
            UPDATE {table_name}
            SET status=?
            WHERE id=? AND user_id=?
            """,

            (status,item_id,user_id)

        )

        conn.commit()

        conn.close()

        return jsonify({

            "success":True,

            "message":"Updated Successfully"

        })


# ==========================================
# HOMEWORK
# ==========================================

@app.route("/homework",methods=["GET","POST"])
def homework():

    return handle_crud(

        "homework",

        ["subject","title","due_date"],

        ["status"]

    )


@app.route("/homework/<int:item_id>",methods=["PUT","DELETE"])
def homework_item(item_id):

    return handle_single_item(

        "homework",

        item_id

    )


# ==========================================
# ASSIGNMENTS
# ==========================================

@app.route("/assignments",methods=["GET","POST"])
def assignments():

    return handle_crud(

        "assignments",

        ["subject","title","submission_date"],

        ["status"]

    )


@app.route("/assignments/<int:item_id>",methods=["PUT","DELETE"])
def assignment_item(item_id):

    return handle_single_item(

        "assignments",

        item_id

    )


# ==========================================
# EXAMS
# ==========================================

@app.route("/exams",methods=["GET","POST"])
def exams():

    return handle_crud(

        "exams",

        ["subject","exam_date"]

    )


@app.route("/exams/<int:item_id>",methods=["DELETE"])
def exam_item(item_id):

    return handle_single_item(

        "exams",

        item_id

    )
# ==========================================
# ATTENDANCE
# ==========================================

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    return handle_crud(

        "attendance",

        ["subject"],

        ["classes_attended", "total_classes"]

    )


@app.route("/attendance/<int:item_id>", methods=["PUT", "DELETE"])
def attendance_item(item_id):

    user_id = get_authenticated_user_id()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Delete Attendance
    if request.method == "DELETE":

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM attendance WHERE id=? AND user_id=?",
            (item_id, user_id)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Attendance Deleted"
        })

    # Update Attendance

    data = request.get_json()

    attended = data.get("classes_attended")
    total = data.get("total_classes")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE attendance
        SET classes_attended=?,
            total_classes=?
        WHERE id=? AND user_id=?
    """, (attended, total, item_id, user_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Attendance Updated"
    })


# ==========================================
# TIMETABLE
# ==========================================

@app.route("/timetable", methods=["GET", "POST"])
def timetable():

    return handle_crud(

        "timetable",

        ["day", "subject", "start_time", "end_time"]

    )


@app.route("/timetable/<int:item_id>", methods=["DELETE"])
def timetable_item(item_id):

    user_id = get_authenticated_user_id()

    if not user_id:
        return jsonify({"error":"Unauthorized"}),401

    conn=get_db_connection()

    cursor=conn.cursor()

    cursor.execute(

        "DELETE FROM timetable WHERE id=? AND user_id=?",

        (item_id,user_id)

    )

    conn.commit()

    conn.close()

    return jsonify({

        "success":True,

        "message":"Timetable Deleted"

    })


# ==========================================
# AI TIMETABLE GENERATOR
# ==========================================

@app.route("/ai-timetable", methods=["POST"])
def ai_timetable():

    user_id = get_authenticated_user_id()

    if not user_id:
        return jsonify({"error":"Unauthorized"}),401

    data = request.get_json()

    subjects = data.get("subjects", [])
    hours = int(data.get("hours", 4))
    wake = data.get("wake", "07:00")

    if len(subjects) == 0:

        return jsonify({
            "error":"No subjects provided"
        }),400

    minutes = (hours * 60) // len(subjects)

    current = datetime.strptime(wake, "%H:%M")
    current += timedelta(hours=1)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM timetable WHERE user_id=?",
        (user_id,)
    )

    schedule=[]

    for subject in subjects:

        start=current.strftime("%I:%M %p")

        end=current+timedelta(minutes=minutes)

        end_time=end.strftime("%I:%M %p")

        cursor.execute("""

            INSERT INTO timetable
            (user_id,day,subject,start_time,end_time)

            VALUES(?,?,?,?,?)

        """,(user_id,"Today",subject,start,end_time))

        schedule.append({

            "subject":subject,

            "start_time":start,

            "end_time":end_time

        })

        current=end+timedelta(minutes=15)

    conn.commit()

    conn.close()

    return jsonify({

        "success":True,

        "message":"AI Timetable Generated",

        "schedule":schedule

    })


# ==========================================
# DASHBOARD SUMMARY
# ==========================================

@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():

    user_id=get_authenticated_user_id()

    if not user_id:
        return jsonify({"error":"Unauthorized"}),401

    conn=get_db_connection()

    cursor=conn.cursor()

    dashboard={}

    tables=[

        "homework",

        "assignments",

        "attendance",

        "exams",

        "timetable"

    ]

    for table in tables:

        cursor.execute(

            f"SELECT COUNT(*) FROM {table} WHERE user_id=?",

            (user_id,)

        )

        dashboard[table]=cursor.fetchone()[0]

    conn.close()

    return jsonify(dashboard)


# ==========================================
# START APPLICATION
# ==========================================

if __name__=="__main__":

    init_db()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
    