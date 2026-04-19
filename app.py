import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import active_config

app = Flask(__name__)
app.config.from_object(active_config)

# ==========================================
# Database Connection Helper
# ==========================================
def get_db_connection():
    try:
        # SQLite uses a local file instead of a server
        connection = sqlite3.connect('database.db', check_same_thread=False)
        # This makes the cursor return dictionary-like row objects
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(f"Error connecting to Database: {e}")
        return None

# ==========================================
# Initialize Database & Admin
# ==========================================
def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Create admin table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT NOT NULL UNIQUE,
            class TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create marks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            marks INTEGER NOT NULL CHECK (marks >= 0 AND marks <= 100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, subject)
        )
        ''')

        # Insert default admin if not exists
        cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
        admin = cursor.fetchone()
        if not admin:
            hashed_pw = generate_password_hash('admin123')
            cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', hashed_pw))
            conn.commit()
            print("Default admin created: admin / admin123")
            
        cursor.close()
        conn.close()

# Try to init DB on startup
with app.app_context():
    init_db()

# ==========================================
# Routes
# ==========================================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed.', 'error')
            return render_template('login.html')

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    stats = {'total_students': 0, 'recent_students': []}
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM students")
        stats['total_students'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC LIMIT 5")
        stats['recent_students'] = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('dashboard.html', stats=stats)

@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        student_class = request.form.get('student_class')

        if not name or not roll_no or not student_class:
            flash('All fields are required.', 'error')
            return render_template('add_student.html')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                hashed_pw = generate_password_hash(roll_no)
                cursor.execute("INSERT INTO students (name, roll_no, class, password) VALUES (?, ?, ?, ?)", 
                               (name, roll_no, student_class, hashed_pw))
                conn.commit()
                flash('Student added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash(f'Roll number {roll_no} already exists.', 'error')
            except Exception as e:
                flash(f'Error adding student: {e}', 'error')
            finally:
                cursor.close()
                conn.close()

    return render_template('add_student.html')

@app.route('/add-marks', methods=['GET', 'POST'])
def add_marks():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    students = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, roll_no, name FROM students ORDER BY roll_no")
        students = cursor.fetchall()
        cursor.close()
        conn.close()

    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        subject = request.form.get('subject')
        marks = request.form.get('marks')

        if not roll_no or not subject or not marks:
            flash('All fields are required.', 'error')
            return render_template('add_marks.html', students=students)

        try:
            marks = int(marks)
            if marks < 0 or marks > 100:
                flash('Marks must be between 0 and 100.', 'error')
                return render_template('add_marks.html', students=students)
        except ValueError:
            flash('Marks must be a number.', 'error')
            return render_template('add_marks.html', students=students)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,))
                student = cursor.fetchone()
                if not student:
                    flash(f'Student with Roll Number {roll_no} not found.', 'error')
                    return render_template('add_marks.html', students=students)
                
                student_id = student['id']
                cursor.execute("INSERT INTO marks (student_id, subject, marks) VALUES (?, ?, ?)",
                               (student_id, subject, marks))
                conn.commit()
                flash('Marks added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash(f'Marks for subject {subject} already exist for this student.', 'error')
            except Exception as e:
                flash(f'Error adding marks: {e}', 'error')
            finally:
                cursor.close()
                conn.close()

    return render_template('add_marks.html', students=students)

def calculate_grade(percentage):
    if percentage >= 90:
        return 'A', '#00ffc8' # Greenish
    elif percentage >= 75:
        return 'B', '#00c6ff' # Cyan
    elif percentage >= 50:
        return 'C', '#ffaa00' # Yellow
    else:
        return 'Fail', '#ff4466' # Red

@app.route('/result/<roll_no>')
def result(roll_no):
    if 'admin_id' not in session:
        if 'student_id' not in session or session.get('student_roll') != roll_no:
            return redirect(url_for('student_login_page'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'error')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    
    # Get student info
    cursor.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
    student = cursor.fetchone()
    
    if not student:
        cursor.close()
        conn.close()
        flash(f'Student with Roll Number {roll_no} not found.', 'error')
        return redirect(url_for('dashboard'))

    # Get student marks
    cursor.execute("SELECT subject, marks FROM marks WHERE student_id = ?", (student['id'],))
    marks = cursor.fetchall()
    
    cursor.close()
    conn.close()

    total_marks = 0
    percentage = 0
    grade = ('N/A', '#fff')
    
    if marks:
        total_marks = sum(item['marks'] for item in marks)
        max_possible = len(marks) * 100
        percentage = (total_marks / max_possible) * 100
        grade = calculate_grade(percentage)

    return render_template('result.html', student=student, marks=marks, 
                           total_marks=total_marks, percentage=round(percentage, 2), grade=grade)

@app.route('/')
def student_login_page():
    if 'student_id' in session:
        return redirect(url_for('student_result'))
    return render_template('student_login.html')

@app.route('/api/student/login', methods=['POST'])
def api_student_login():
    data = request.get_json()
    if not data:
        return {'success': False, 'message': 'Invalid data'}, 400
        
    enrollment = data.get('enrollment')
    password = data.get('password')
    
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'message': 'Database connection failed'}, 500
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE roll_no = ?", (enrollment,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if student and check_password_hash(student['password'], password):
        session['student_id'] = student['id']
        session['student_roll'] = student['roll_no']
        return {'success': True, 'message': 'Login successful'}
    else:
        return {'success': False, 'message': 'Invalid enrollment number or password'}, 401

@app.route('/my-result')
def student_result():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))
    return result(session['student_roll'])

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
