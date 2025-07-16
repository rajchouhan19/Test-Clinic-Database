from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, g
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Database Connection Management ---
def get_db():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="1234",
                database="hospital_db"
            )
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            g.db = None
    return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Main and Login Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    try:
        db = get_db()
        if not db:
            flash("Cannot connect to the database.", "danger")
            return redirect(url_for('index'))
            
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s AND role = %s", (username, password, role))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['user'] = user['username']
            session['role'] = user['role']
            flash("Login successful!", "success")
            if user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user['role'] == 'nurse':
                return redirect(url_for('nurse_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash("Invalid credentials or role.", "danger")
            return redirect(url_for('index'))
    except mysql.connector.Error as err:
        flash(f"A database error occurred during login: {err}", "danger")
        return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# --- Registration ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        username = request.form['username']
        password = request.form['password']
        try:
            db = get_db()
            if not db:
                flash("Cannot connect to the database.", "danger")
                return redirect(url_for('register'))

            cursor = db.cursor()
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'patient')", (username, password))
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO patients (first_name, last_name, age, gender, user_id) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, age, gender, user_id)
            )
            db.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            flash(f"A database error occurred during registration: {err}", "danger")
            return redirect(url_for('register'))
    return render_template("register.html")

# --- Dashboards ---
@app.route("/doctor_dashboard")
def doctor_dashboard():
    if 'user' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))
    try:
        db = get_db()
        if not db:
            flash("Cannot connect to the database.", "danger")
            return render_template("doctor_dashboard.html", patients=[], prescriptions=[])
        
        cursor = db.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT p.*, u.username FROM patients p LEFT JOIN users u ON p.user_id = u.id")
        patients = cursor.fetchall()
        cursor.execute("SELECT * FROM prescriptions")
        prescriptions = cursor.fetchall()
        return render_template("doctor_dashboard.html", patients=patients, prescriptions=prescriptions)
    except mysql.connector.Error as err:
        flash(f"Could not load doctor dashboard: {err}", "danger")
        return render_template("doctor_dashboard.html", patients=[], prescriptions=[])

@app.route("/nurse_dashboard")
def nurse_dashboard():
    if 'user' not in session or session.get('role') != 'nurse':
        return redirect(url_for('index'))
    try:
        db = get_db()
        if not db:
            flash("Cannot connect to the database.", "danger")
            return render_template("nurse_dashboard.html", patients=[], test_results=[])

        cursor = db.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM patients WHERE is_active = TRUE")
        patients = cursor.fetchall()
        cursor.execute("SELECT * FROM test_results")
        test_results = cursor.fetchall()
        return render_template("nurse_dashboard.html", patients=patients, test_results=test_results)
    except mysql.connector.Error as err:
        flash(f"Could not load nurse dashboard: {err}", "danger")
        return render_template("nurse_dashboard.html", patients=[], test_results=[])

@app.route("/patient_dashboard")
def patient_dashboard():
    if 'user' not in session or session.get('role') != 'patient':
        return redirect(url_for('index'))
    try:
        db = get_db()
        if not db:
            flash("Cannot connect to the database.", "danger")
            return render_template("patient_dashboard.html", patient={}, prescriptions=[], test_results=[])

        cursor = db.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM patients WHERE user_id = %s", (session['user_id'],))
        patient_details = cursor.fetchone()
        
        prescriptions = []
        test_results = []
        if patient_details:
            patient_pk_id = patient_details['id']
            cursor.execute("SELECT * FROM prescriptions WHERE patient_id = %s AND is_active = TRUE", (patient_pk_id,))
            prescriptions = cursor.fetchall()
            cursor.execute("SELECT * FROM test_results WHERE patient_id = %s", (patient_pk_id,))
            test_results = cursor.fetchall()
        else:
            flash("Could not find your patient record.", "warning")

        return render_template("patient_dashboard.html", patient=patient_details, prescriptions=prescriptions, test_results=test_results)
    except mysql.connector.Error as err:
        flash(f"Could not load your dashboard: {err}", "danger")
        return render_template("patient_dashboard.html", patient={}, prescriptions=[], test_results=[])


# --- Unified Patient View ---
@app.route("/patient_view/<int:patient_id>")
def patient_view(patient_id):
    if 'user' not in session or session.get('role') not in ['doctor', 'nurse']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True, buffered=True)

        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            flash("Patient not found.", "danger")
            return redirect(url_for(session['role'] + '_dashboard'))

        cursor.execute("""
            SELECT pr.*, u.username AS doctor_name
            FROM prescriptions pr
            LEFT JOIN users u ON pr.doctor_id = u.id
            WHERE pr.patient_id = %s
        """, (patient_id,))
        prescriptions = cursor.fetchall()

        cursor.execute("""
            SELECT tr.*, u.username AS nurse_name
            FROM test_results tr
            LEFT JOIN users u ON tr.nurse_id = u.id
            WHERE tr.patient_id = %s
        """, (patient_id,))
        test_results = cursor.fetchall()

        return render_template("patient_view.html", patient=patient, prescriptions=prescriptions, test_results=test_results)

    except mysql.connector.Error as err:
        flash(f"Database error while fetching patient data: {err}", "danger")
        return redirect(url_for(session['role'] + '_dashboard'))

# --- Form and Action Routes ---
@app.route("/create_user", methods=["POST"])
def create_user():
    if 'user' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))
    try:
        db = get_db()
        if not db:
            flash("Cannot connect to the database.", "danger")
            return redirect(url_for('doctor_dashboard'))

        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        
        if role == 'patient':
            user_id = cursor.lastrowid
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            age = request.form['age']
            gender = request.form['gender']
            cursor.execute(
                "INSERT INTO patients (first_name, last_name, age, gender, user_id) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, age, gender, user_id)
            )
        db.commit()
        flash(f"{role.title()} account created successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Failed to create user: {err}", "danger")
    return redirect(url_for('doctor_dashboard'))

@app.route("/update_patient_details", methods=["POST"])
def update_patient_details():
    if 'user' not in session or session.get('role') != 'patient':
        return redirect(url_for('index'))
    try:
        db = get_db()
        if not db:
            flash("Cannot connect to the database.", "danger")
            return redirect(url_for('patient_dashboard'))

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        cursor = db.cursor()
        cursor.execute(
            "UPDATE patients SET first_name = %s, last_name = %s, age = %s, gender = %s WHERE user_id = %s",
            (first_name, last_name, age, gender, session['user_id'])
        )
        db.commit()
        flash("Your details have been updated successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Failed to update details: {err}", "danger")
    return redirect(url_for('patient_dashboard'))

@app.route("/toggle_patient_status/<int:patient_id>", methods=["POST"])
def toggle_patient_status(patient_id):
    if 'user' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE patients SET is_active = NOT is_active WHERE id = %s", (patient_id,))
        db.commit()
        flash("Patient status updated.", "success")
    except mysql.connector.Error as err:
        flash(f"Failed to update patient status: {err}", "danger")
    return redirect(url_for('doctor_dashboard'))

@app.route("/toggle_prescription_status/<int:prescription_id>", methods=["POST"])
def toggle_prescription_status(prescription_id):
    if 'user' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE prescriptions SET is_active = NOT is_active WHERE id = %s", (prescription_id,))
        db.commit()
        flash("Prescription status updated.", "success")
    except mysql.connector.Error as err:
        flash(f"Failed to update prescription status: {err}", "danger")
    return redirect(url_for('doctor_dashboard'))

@app.route("/add_prescription_form", methods=["POST"])
def add_prescription_form():
    if 'user' not in session or session.get('role') != 'doctor':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))
    try:
        db = get_db()
        cursor = db.cursor()
        patient_id = request.form['patient_id']
        drug_name = request.form['drug_name']
        doctor_id = session['user_id']
        
        cursor.execute(
            "INSERT INTO prescriptions (patient_id, doctor_id, drug_name, date) VALUES (%s, %s, %s, NOW())",
            (patient_id, doctor_id, drug_name)
        )
        db.commit()
        flash("Prescription added successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Failed to add prescription: {err}", "danger")
    
    return redirect(url_for('doctor_dashboard'))

@app.route("/add_test_result_form", methods=["POST"])
def add_test_result_form():
    if 'user' not in session or session.get('role') != 'nurse':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))
    try:
        db = get_db()
        cursor = db.cursor()
        patient_id = request.form['patient_id']
        test_name = request.form['test_name']
        result = request.form['result']
        nurse_id = session['user_id']
        
        cursor.execute(
            "INSERT INTO test_results (patient_id, nurse_id, test_name, result, date) VALUES (%s, %s, %s, %s, NOW())",
            (patient_id, nurse_id, test_name, result)
        )
        db.commit()
        flash("Test result recorded successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Failed to record test result: {err}", "danger")

    return redirect(url_for('nurse_dashboard'))

# --- Main Execution ---
if __name__ == "__main__":
    app.run(debug=True)
