"""
Task Management System — Flask middleware
==========================================
Connects the HTML/CSS/JS frontend to a MySQL database.

Tables used (see schema.sql):
  - admin_login      : login credentials for the admin
  - employees        : list of employees
  - task_management  : tasks, each linked to an employee_id (FK)

Setup:
  1. pip install -r requirements.txt
  2. Create the database:  mysql -u root -p < schema.sql
  3. Fill in DB_CONFIG below with your MySQL credentials
  4. python app.py
  5. Open http://localhost:5000
     Default login -> username: admin | password: admin123
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"  # needed for session cookies

# ------------------------------------------------------------------
# MySQL connection settings — edit these to match your local setup
# ------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "task_management",
}


def get_db():
    """Open a fresh MySQL connection for the current request."""
    return mysql.connector.connect(**DB_CONFIG)


def login_required(view):
    """Simple decorator: redirect to /login if no active admin session."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


# ------------------------------------------------------------------
# Auth routes
# ------------------------------------------------------------------
@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT admin_id, username, password_hash FROM admin_login WHERE username = %s",
            (username,),
        )
        admin = cur.fetchone()
        cur.close()
        conn.close()
    except Error as e:
        return jsonify({"ok": False, "error": f"Database error: {e}"}), 500

    if admin and check_password_hash(admin["password_hash"], password):
        session["admin_id"] = admin["admin_id"]
        session["username"] = admin["username"]
        return jsonify({"ok": True, "redirect": url_for("dashboard")})

    return jsonify({"ok": False, "error": "Invalid username or password"}), 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------
# Dashboard (task management page)
# ------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))


# ------------------------------------------------------------------
# API: employees (used to populate the "Employee name" dropdown)
# ------------------------------------------------------------------
@app.route("/api/employees", methods=["GET"])
@login_required
def api_employees():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT employee_id, employee_name FROM employees ORDER BY employee_name")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------
# API: tasks — full CRUD, backing the Task Management screen
# ------------------------------------------------------------------
@app.route("/api/tasks", methods=["GET"])
@login_required
def api_tasks_list():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT t.task_id, t.task_title, t.completed, t.created_at,
                   e.employee_id, e.employee_name
            FROM task_management t
            JOIN employees e ON e.employee_id = t.employee_id
            ORDER BY t.task_id DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for r in rows:
            r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks", methods=["POST"])
@login_required
def api_tasks_create():
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    task_title = (data.get("task_title") or "").strip()
    completed = "true" if str(data.get("completed")).lower() == "true" else "false"

    if not employee_id or not task_title:
        return jsonify({"error": "employee_id and task_title are required"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO task_management (employee_id, task_title, completed) VALUES (%s, %s, %s)",
            (employee_id, task_title, completed),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return jsonify({"ok": True, "task_id": new_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def api_tasks_update(task_id):
    data = request.get_json(silent=True) or {}
    fields, values = [], []

    if "employee_id" in data:
        fields.append("employee_id = %s")
        values.append(data["employee_id"])
    if "task_title" in data:
        fields.append("task_title = %s")
        values.append(data["task_title"])
    if "completed" in data:
        fields.append("completed = %s")
        values.append("true" if str(data["completed"]).lower() == "true" else "false")

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    values.append(task_id)
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(f"UPDATE task_management SET {', '.join(fields)} WHERE task_id = %s", values)
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()
        return jsonify({"ok": True, "updated": affected})
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def api_tasks_delete(task_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM task_management WHERE task_id = %s", (task_id,))
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()
        return jsonify({"ok": True, "deleted": affected})
    except Error as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
