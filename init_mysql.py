
import mysql.connector
from config import active_config

def init_db():
    try:
        # Connect to MySQL without database first to create it
        conn = mysql.connector.connect(
            host=active_config.MYSQL_HOST,
            user=active_config.MYSQL_USER,
            password=active_config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {active_config.MYSQL_DATABASE}")
        cursor.execute(f"USE {active_config.MYSQL_DATABASE}")
        
        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll_no VARCHAR(30) NOT NULL UNIQUE,
            class VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) DEFAULT NULL,
            phone VARCHAR(20) DEFAULT NULL,
            dob VARCHAR(20) DEFAULT NULL,
            address VARCHAR(255) DEFAULT NULL,
            current_semester INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            subject VARCHAR(100) NOT NULL,
            marks INT NOT NULL,
            semester INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE KEY unique_student_subject (student_id, subject)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_forms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            semester INT NOT NULL,
            status VARCHAR(20) DEFAULT 'approved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE KEY unique_student_semester_form (student_id, semester)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_form_subjects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            form_id INT NOT NULL,
            subject_name VARCHAR(100) NOT NULL,
            exam_date VARCHAR(20) DEFAULT NULL,
            FOREIGN KEY (form_id) REFERENCES exam_forms(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            destination VARCHAR(200) NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        """)

        # Add columns to students if they don't exist (migration for existing DBs)
        alter_columns = [
            "ALTER TABLE students ADD COLUMN email VARCHAR(100) DEFAULT NULL",
            "ALTER TABLE students ADD COLUMN phone VARCHAR(20) DEFAULT NULL",
            "ALTER TABLE students ADD COLUMN dob VARCHAR(20) DEFAULT NULL",
            "ALTER TABLE students ADD COLUMN address VARCHAR(255) DEFAULT NULL",
            "ALTER TABLE students ADD COLUMN current_semester INT DEFAULT 1",
            "ALTER TABLE marks ADD COLUMN semester INT DEFAULT 1",
        ]
        for sql in alter_columns:
            try:
                cursor.execute(sql)
            except mysql.connector.Error:
                pass  # Column already exists
        
        # Add default admin
        from werkzeug.security import generate_password_hash
        cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash('admin123')
            cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", ('admin', hashed_pw))
            conn.commit()
            print("Admin created: admin / admin123")
            
        print("Database initialized successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_db()
