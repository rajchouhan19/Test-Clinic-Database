# Clinic Management System

A web application built with Python and Flask to streamline core operations for a medical clinic. This project provides a multi-user environment with distinct portals and functionalities for Doctors, Nurses, and Patients to manage records, prescriptions, and lab results efficiently.

## Key Features

* **Role-Based Access Control:** Secure login and tailored dashboards for Doctor, Nurse, and Patient roles.
* **Patient Management:** Doctors can view all patient records (active and inactive), create new user accounts for any role, and deactivate or reactivate patient profiles using a soft-delete system.
* **Clinical Records Management:** Doctors can issue new prescriptions, and nurses can record test results. A unified patient view page allows clinical staff to see a patient's complete history at a glance.
* **Patient Portal:** Patients have their own dashboard to view their medical history and update their personal details.

## Technologies Used

* **Backend:** Python, Flask
* **Database:** MySQL
* **Frontend:** HTML, CSS, Bootstrap 5

## Setup and Installation


1.  **Install Dependencies:**
    ```bash
    pip install Flask 
    pip install Flask mysql-connector-python
    ```

2.  **Database Setup:**
    * Ensure a MySQL server is running.
    * Create a database (e.g., `clinic_db`).
    * Execute the table schemas provided in a `database_setup.sql` file to create all necessary tables.
    * Update your database credentials (`host`, `user`, `password`, `database`) inside the `get_db()` function in the main Python file.

3.  **Run the Application in CMD:**
    ```bash
    python file_app.py
    ```
    The application will be available at `http://127.0.0.1:5000`.

4.  **Important Note:**

    Do add initial doctor/admin in sql editor using:
    ```bash
    INSERT INTO users (username, password, role)
	VALUES ('doctor', 'doctor123', 'doctor');

    ```
