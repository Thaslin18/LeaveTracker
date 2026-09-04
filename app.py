import os
import psycopg
from psycopg.rows import dict_row
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"


DATABASE_URL = "postgresql://neondb_owner:npg_2oR1XHvBsjkS@ep-curly-frost-az14fnlm.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_connection():
    return psycopg.connect(DATABASE_URL)

def fetch_all(sql, values=()):
    connection = get_connection()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(sql, values)
            return cursor.fetchall()
    finally:
        connection.close()

def fetch_one(sql, values=()):
    rows = fetch_all(sql, values)
    return rows[0] if rows else None

def execute(sql, values=(), fetch_id=False):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            connection.commit()
            if fetch_id:
                row = cursor.fetchone()
                return row[0] if row else None
            return cursor.rowcount
    finally:
        connection.close()

@app.get("/")
def home():
    return render_template("home.html")

# ========================= EMPLOYEES MODULE =========================
@app.get("/employees")
def employees():
    rows = fetch_all("SELECT id, name, email, department FROM employees ORDER BY id DESC")
    return render_template("employees.html", employees=rows)

@app.route("/employees/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        if not name or not email or not department:
            flash("All employee fields are required.", "error")
            return render_template("employee_form.html")
        execute(
            "INSERT INTO employees (name, email, department) VALUES (%s, %s, %s)",
            (name, email, department),
        )
        flash("Employee added.", "success")
        return redirect(url_for("employees"))
    return render_template("employee_form.html")

@app.post("/employees/<int:employee_id>/delete")
def delete_employee(employee_id):
    execute("DELETE FROM employees WHERE id=%s", (employee_id,))
    flash("Employee deleted.", "success")
    return redirect(url_for("employees"))

@app.get("/api/employees")
def api_employees():
    return jsonify(fetch_all("SELECT id, name, email, department FROM employees"))

@app.post("/api/employees")
def api_add_employee():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    department = str(data.get("department", "")).strip()
    if not name or not email or not department:
        return jsonify(error="name, email, and department are required"), 400
    
    employee_id = execute(
        "INSERT INTO employees (name, email, department) VALUES (%s, %s, %s) RETURNING id",
        (name, email, department),
        fetch_id=True
    )
    return jsonify(id=employee_id, name=name, email=email, department=department), 201

@app.put("/api/employees/<int:employee_id>")
def api_update_employee(employee_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    department = str(data.get("department", "")).strip()
    if not name or not email or not department:
        return jsonify(error="name, email, and department are required"), 400
    if not fetch_one("SELECT id FROM employees WHERE id=%s", (employee_id,)):
        return jsonify(error="employee not found"), 404
    
    execute(
        "UPDATE employees SET name=%s, email=%s, department=%s WHERE id=%s",
        (name, email, department, employee_id),
    )
    return jsonify(id=employee_id, name=name, email=email, department=department)

@app.delete("/api/employees/<int:employee_id>")
def api_delete_employee(employee_id):
    if not fetch_one("SELECT id FROM employees WHERE id=%s", (employee_id,)):
        return jsonify(error="employee not found"), 404
    execute("DELETE FROM employees WHERE id=%s", (employee_id,))
    return jsonify(message="employee deleted")

# ========================= LEAVE TYPES MODULE =========================
@app.get("/leave-types")
def leave_types():
    rows = fetch_all("SELECT id, name, days_allowed, description FROM leave_types ORDER BY id DESC")
    return render_template("leave_types.html", leave_types=rows)

@app.route("/leave-types/add", methods=["GET", "POST"])
def add_leave_type():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        days_allowed = request.form.get("days_allowed", "").strip()
        description = request.form.get("description", "").strip()
        if not name or not days_allowed.isdigit() or not description:
            flash("Enter name, numeric days allowed, and description.", "error")
            return render_template("leave_type_form.html")
        
        execute(
            "INSERT INTO leave_types (name, days_allowed, description) VALUES (%s, %s, %s)",
            (name, int(days_allowed), description),
        )
        flash("Leave type added.", "success")
        return redirect(url_for("leave_types"))
    return render_template("leave_type_form.html")

@app.post("/leave-types/<int:leave_type_id>/delete")
def delete_leave_type(leave_type_id):
    execute("DELETE FROM leave_types WHERE id=%s", (leave_type_id,))
    flash("Leave type deleted.", "success")
    return redirect(url_for("leave_types"))

@app.get("/api/leave-types")
def api_leave_types():
    return jsonify(fetch_all("SELECT id, name, days_allowed, description FROM leave_types"))

@app.post("/api/leave-types")
def api_add_leave_type():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    days_allowed = data.get("days_allowed")
    description = str(data.get("description", "")).strip()
    if not name or not isinstance(days_allowed, int) or not description:
        return jsonify(error="name, integer days_allowed, and description are required"), 400
    
    leave_type_id = execute(
        "INSERT INTO leave_types (name, days_allowed, description) VALUES (%s, %s, %s) RETURNING id",
        (name, days_allowed, description),
        fetch_id=True
    )
    return jsonify(id=leave_type_id, name=name, days_allowed=days_allowed, description=description), 201

@app.put("/api/leave-types/<int:leave_type_id>")
def api_update_leave_type(leave_type_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    days_allowed = data.get("days_allowed")
    description = str(data.get("description", "")).strip()
    if not name or not isinstance(days_allowed, int) or not description:
        return jsonify(error="name, integer days_allowed, and description are required"), 400
    if not fetch_one("SELECT id FROM leave_types WHERE id=%s", (leave_type_id,)):
        return jsonify(error="leave type not found"), 404
    
    execute(
        "UPDATE leave_types SET name=%s, days_allowed=%s, description=%s WHERE id=%s",
        (name, days_allowed, description, leave_type_id),
    )
    return jsonify(id=leave_type_id, name=name, days_allowed=days_allowed, description=description)

@app.delete("/api/leave-types/<int:leave_type_id>")
def api_delete_leave_type(leave_type_id):
    if not fetch_one("SELECT id FROM leave_types WHERE id=%s", (leave_type_id,)):
        return jsonify(error="leave type not found"), 404
    execute("DELETE FROM leave_types WHERE id=%s", (leave_type_id,))
    return jsonify(message="leave type deleted")

# ========================= LEAVE REQUESTS MODULE =========================
@app.get("/leave-requests")
def leave_requests():
    rows = fetch_all("""
        SELECT lr.id, lr.employee_id, lr.leave_type_id, lr.leave_date,
               e.name AS employee_name, lt.name AS leave_type_name
        FROM leave_requests lr
        JOIN employees e ON e.id = lr.employee_id
        JOIN leave_types lt ON lt.id = lr.leave_type_id
        ORDER BY lr.id DESC
    """)
    return render_template("leave_requests.html", leave_requests=rows)

@app.route("/leave-requests/add", methods=["GET", "POST"])
def add_leave_request():
    employee_rows = fetch_all("SELECT id, name FROM employees ORDER BY name")
    type_rows = fetch_all("SELECT id, name FROM leave_types ORDER BY name")
    if request.method == "POST":
        employee_id = request.form.get("employee_id", "")
        leave_type_id = request.form.get("leave_type_id", "")
        leave_date = request.form.get("leave_date", "")
        if not employee_id.isdigit() or not leave_type_id.isdigit() or not leave_date:
            flash("Choose employee, leave type, and date.", "error")
            return render_template("leave_request_form.html", employees=employee_rows, leave_types=type_rows)
        
        execute(
            "INSERT INTO leave_requests (employee_id, leave_type_id, leave_date) VALUES (%s, %s, %s)",
            (int(employee_id), int(leave_type_id), leave_date),
        )
        flash("Leave request added.", "success")
        return redirect(url_for("leave_requests"))
    return render_template("leave_request_form.html", employees=employee_rows, leave_types=type_rows)

@app.post("/leave-requests/<int:request_id>/delete")
def delete_leave_request(request_id):
    execute("DELETE FROM leave_requests WHERE id=%s", (request_id,))
    flash("Leave request deleted.", "success")
    return redirect(url_for("leave_requests"))

@app.get("/api/leave-requests")
def api_leave_requests():
    return jsonify(fetch_all("SELECT id, employee_id, leave_type_id, leave_date FROM leave_requests"))

@app.post("/api/leave-requests")
def api_add_leave_request():
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    leave_type_id = data.get("leave_type_id")
    leave_date = str(data.get("leave_date", "")).strip()
    if not isinstance(employee_id, int) or not isinstance(leave_type_id, int) or not leave_date:
        return jsonify(error="integer employee_id, integer leave_type_id, and leave_date are required"), 400
    if not fetch_one("SELECT id FROM employees WHERE id=%s", (employee_id,)):
        return jsonify(error="employee_id does not exist"), 400
    if not fetch_one("SELECT id FROM leave_types WHERE id=%s", (leave_type_id,)):
        return jsonify(error="leave_type_id does not exist"), 400
    
    request_id = execute(
        "INSERT INTO leave_requests (employee_id, leave_type_id, leave_date) VALUES (%s, %s, %s) RETURNING id",
        (employee_id, leave_type_id, leave_date),
        fetch_id=True
    )
    return jsonify(id=request_id, employee_id=employee_id, leave_type_id=leave_type_id, leave_date=leave_date), 201

@app.delete("/api/leave-requests/<int:request_id>")
def api_delete_leave_request(request_id):
    if not fetch_one("SELECT id FROM leave_requests WHERE id=%s", (request_id,)):
        return jsonify(error="leave request not found"), 404
    execute("DELETE FROM leave_requests WHERE id=%s", (request_id,))
    return jsonify(message="leave request deleted")

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", message="Page not found."), 404

if __name__ == "__main__":
    app.run(debug=True)