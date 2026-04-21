import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import active_config

app = Flask(__name__)
app.config.from_object(active_config)

# ==========================================
# Database Connection Helper
# ==========================================
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        conn.row_factory = dict_factory
        return conn
    except Exception as e:
        print(f"CRITICAL: Database connection failed! {e}")
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
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            roll_no VARCHAR(30) NOT NULL UNIQUE,
            class VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) DEFAULT NULL,
            phone VARCHAR(20) DEFAULT NULL,
            dob VARCHAR(20) DEFAULT NULL,
            address VARCHAR(255) DEFAULT NULL,
            current_semester INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create marks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject VARCHAR(100) NOT NULL,
            marks INTEGER NOT NULL,
            semester INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, subject)
        )
        ''')

        # Create exam_forms table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'approved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, semester)
        )
        ''')

        # Create exam_form_subjects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_form_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER NOT NULL,
            subject_name VARCHAR(100) NOT NULL,
            exam_date VARCHAR(20) DEFAULT NULL,
            FOREIGN KEY (form_id) REFERENCES exam_forms(id) ON DELETE CASCADE
        )
        ''')

        # Create migration_requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            destination VARCHAR(200) NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        ''')

        # Add columns to students if they don't exist (migration for existing DBs)
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN email VARCHAR(100) DEFAULT NULL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN phone VARCHAR(20) DEFAULT NULL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN dob VARCHAR(20) DEFAULT NULL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN address VARCHAR(255) DEFAULT NULL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN current_semester INTEGER DEFAULT 1")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE marks ADD COLUMN semester INTEGER DEFAULT 1")
        except:
            pass

        # Insert default admin if not exists
        cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
        admin = cursor.fetchone()
        if not admin:
            hashed_pw = generate_password_hash('admin123')
            cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', hashed_pw))
            conn.commit()
            print("Default admin created: admin / admin123")
        
        # Ensure marks table has correct unique constraint (if possible)
        # Note: SQLite doesn't support ALTER TABLE for constraints. 
        # We'll just ensure the semester column is there and use logic in code.
            
        cursor.close()
        conn.close()

# Try to init DB on startup
with app.app_context():
    init_db()

# ==========================================
# Helper: Get student data from session
# ==========================================
def get_current_student():
    """Fetch full student record from session student_id."""
    if 'student_id' not in session:
        return None
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE id = ?", (session['student_id'],))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return student

# ==========================================
# Available subjects per semester (configurable)
# ==========================================
SEMESTER_SUBJECTS = {
    1: ['Mathematics I', 'Physics', 'Chemistry', 'English', 'Computer Fundamentals'],
    2: ['Mathematics II', 'Data Structures', 'Digital Electronics', 'Communication Skills', 'Environmental Science'],
    3: ['Discrete Mathematics', 'OOP with Java', 'Computer Architecture', 'Database Systems', 'Operating Systems'],
    4: ['Design & Analysis of Algorithms', 'Software Engineering', 'Computer Networks', 'Theory of Computation', 'Statistics'],
    5: ['Compiler Design', 'Machine Learning', 'Web Technologies', 'Cryptography', 'Cloud Computing'],
    6: ['Artificial Intelligence', 'Big Data Analytics', 'Mobile App Development', 'Cyber Security', 'IoT'],
    7: ['Deep Learning', 'Natural Language Processing', 'Blockchain', 'Project Management', 'Elective I'],
    8: ['Major Project', 'Internship', 'Elective II', 'Seminar', 'Ethics in Computing'],
}

def calculate_grade(percentage):
    if percentage >= 90:
        return 'A', '#00ffc8', '#00ffc855', '#00ffc888' # Greenish
    elif percentage >= 75:
        return 'B', '#00c6ff', '#00c6ff55', '#00c6ff88' # Cyan
    elif percentage >= 50:
        return 'C', '#ffaa00', '#ffaa0055', '#ffaa0088' # Yellow
    else:
        return 'Fail', '#ff4466', '#ff446655', '#ff446688' # Red


# ==========================================
# ADMIN Routes (unchanged)
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
            except sqlite3.Error as e:
                if "UNIQUE constraint failed" in str(e): # Duplicate entry
                    flash(f'Roll number {roll_no} already exists.', 'error')
                else:
                    flash(f'Error adding student: {e}', 'error')
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
        semester = request.form.get('semester', type=int) or 1

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
                cursor.execute("INSERT INTO marks (student_id, subject, marks, semester) VALUES (?, ?, ?, ?)",
                               (student_id, subject, marks, semester))
                conn.commit()
                flash('Marks added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.Error as e:
                if "UNIQUE constraint failed" in str(e): # Duplicate entry
                    flash(f'Marks for subject {subject} already exist for this student.', 'error')
                else:
                    flash(f'Error adding marks: {e}', 'error')
            except Exception as e:
                flash(f'Error adding marks: {e}', 'error')
            finally:
                cursor.close()
                conn.close()

    return render_template('add_marks.html', students=students)

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

    # Get student marks for their current semester or all marks
    cursor.execute("SELECT subject, marks, semester FROM marks WHERE student_id = ? ORDER BY semester DESC", (student['id'],))
    marks = cursor.fetchall()
    
    cursor.close()
    conn.close()

    total_marks = 0
    percentage = 0
    grade = ('N/A', '#ffffff', '#ffffff55', '#ffffff88')
    
    if marks:
        total_marks = sum(item['marks'] for item in marks)
        max_possible = len(marks) * 100
        percentage = (total_marks / max_possible) * 100
        grade = calculate_grade(percentage)

    return render_template('result.html', student=student, marks=marks, 
                           total_marks=total_marks, percentage=round(percentage, 2), grade=grade)


# ==========================================
# STUDENT AUTH Routes
# ==========================================

@app.route('/')
def student_login_page():
    if 'student_id' in session:
        return redirect(url_for('student_dashboard'))
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

@app.route('/student/logout')
def student_logout():
    session.pop('student_id', None)
    session.pop('student_roll', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('student_login_page'))

@app.route('/my-result')
def student_result():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))
    return result(session['student_roll'])


# ==========================================
# STUDENT PORTAL Routes
# ==========================================

@app.route('/student/dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))
    
    student = get_current_student()
    if not student:
        return redirect(url_for('student_login_page'))
    
    current_semester = student.get('current_semester', 1) or 1

    conn = get_db_connection()
    total_subjects = 0
    forms_count = 0
    pending_count = 0

    if conn:
        cursor = conn.cursor()
        # Total subjects with marks
        cursor.execute("SELECT COUNT(*) as c FROM marks WHERE student_id = ?", (student['id'],))
        total_subjects = cursor.fetchone()['c']
        # Forms submitted
        cursor.execute("SELECT COUNT(*) as c FROM exam_forms WHERE student_id = ?", (student['id'],))
        forms_count = cursor.fetchone()['c']
        # Pending migration requests
        cursor.execute("SELECT COUNT(*) as c FROM migration_requests WHERE student_id = ? AND status = 'pending'", (student['id'],))
        pending_count = cursor.fetchone()['c']
        cursor.close()
        conn.close()

    return render_template('student_dashboard.html',
        student=student,
        active_page='dashboard',
        current_semester=current_semester,
        total_subjects=total_subjects,
        forms_count=forms_count,
        pending_count=pending_count
    )


@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('dob', '').strip()
        address = request.form.get('address', '').strip()

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE students SET email=?, phone=?, dob=?, address=? WHERE id=?",
                (email or None, phone or None, dob or None, address or None, session['student_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Profile updated successfully!', 'success')
        else:
            flash('Database connection failed.', 'error')

    student = get_current_student()
    return render_template('student_profile.html',
        student=student,
        active_page='profile'
    )


@app.route('/student/semester')
def student_semester_page():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))

    student = get_current_student()
    semester = request.args.get('semester', type=int)

    if semester and 1 <= semester <= 8:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET current_semester = ? WHERE id = ?", (semester, session['student_id']))
            conn.commit()
            cursor.close()
            conn.close()
            flash(f'Semester updated to Semester {semester}', 'success')
            return redirect(url_for('student_semester_page'))

    student = get_current_student()
    current_semester = student.get('current_semester', 1) or 1

    return render_template('student_semester.html',
        student=student,
        active_page='semester',
        current_semester=current_semester
    )


@app.route('/student/form-fillup', methods=['GET', 'POST'])
def student_form_fillup():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))

    student = get_current_student()
    current_semester = student.get('current_semester', 1) or 1
    available_subjects = SEMESTER_SUBJECTS.get(current_semester, [])

    conn = get_db_connection()
    existing_form = None
    form_subjects = []

    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exam_forms WHERE student_id = ? AND semester = ?",
                       (student['id'], current_semester))
        existing_form = cursor.fetchone()

        if existing_form:
            cursor.execute("SELECT * FROM exam_form_subjects WHERE form_id = ?", (existing_form['id'],))
            form_subjects = cursor.fetchall()

        cursor.close()
        conn.close()

    if request.method == 'POST' and not existing_form:
        subjects = request.form.getlist('subjects')
        if not subjects:
            flash('Please select at least one subject.', 'error')
            return render_template('student_form_fillup.html',
                student=student, active_page='form',
                current_semester=current_semester,
                available_subjects=available_subjects,
                existing_form=None, form_subjects=[]
            )

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO exam_forms (student_id, semester, status) VALUES (?, ?, 'approved')",
                    (student['id'], current_semester)
                )
                form_id = cursor.lastrowid
                for subj in subjects:
                    cursor.execute(
                        "INSERT INTO exam_form_subjects (form_id, subject_name) VALUES (?, ?)",
                        (form_id, subj)
                    )
                conn.commit()
                flash('Exam form submitted successfully!', 'success')
                return redirect(url_for('student_form_fillup'))
            except Exception as e:
                flash(f'Error submitting form: {e}', 'error')
            finally:
                cursor.close()
                conn.close()

    return render_template('student_form_fillup.html',
        student=student,
        active_page='form',
        current_semester=current_semester,
        available_subjects=available_subjects,
        existing_form=existing_form,
        form_subjects=form_subjects
    )


@app.route('/student/admit-card')
def student_admit_card():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))

    student = get_current_student()
    current_semester = student.get('current_semester', 1) or 1

    conn = get_db_connection()
    admit_card = None
    subjects = []

    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exam_forms WHERE student_id = ? AND semester = ?",
                       (student['id'], current_semester))
        admit_card = cursor.fetchone()

        if admit_card:
            cursor.execute("SELECT * FROM exam_form_subjects WHERE form_id = ?", (admit_card['id'],))
            subjects = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template('student_admit_card.html',
        student=student,
        active_page='admit',
        current_semester=current_semester,
        admit_card=admit_card,
        subjects=subjects
    )


@app.route('/student/result')
def student_result_page():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))

    student = get_current_student()
    current_semester = student.get('current_semester', 1) or 1

    conn = get_db_connection()
    marks = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT subject, marks, semester FROM marks WHERE student_id = ? AND semester = ?", 
                       (student['id'], current_semester))
        marks = cursor.fetchall()
        cursor.close()
        conn.close()

    total_marks = 0
    percentage = 0
    grade_letter = 'N/A'
    grade_color = '#fff'

    if marks:
        total_marks = sum(m['marks'] for m in marks)
        max_possible = len(marks) * 100
        percentage = round((total_marks / max_possible) * 100, 2)
        grade_letter, grade_color = calculate_grade(percentage)

    return render_template('student_result_portal.html',
        student=student,
        active_page='result',
        current_semester=current_semester,
        marks=marks,
        total_marks=total_marks,
        percentage=percentage,
        grade_letter=grade_letter,
        grade_color=grade_color
    )


@app.route('/student/migration', methods=['GET', 'POST'])
def student_migration():
    if 'student_id' not in session:
        return redirect(url_for('student_login_page'))

    student = get_current_student()

    conn = get_db_connection()
    existing_request = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM migration_requests WHERE student_id = ? ORDER BY created_at DESC LIMIT 1",
                       (student['id'],))
        existing_request = cursor.fetchone()
        cursor.close()
        conn.close()

    if request.method == 'POST' and not existing_request:
        destination = request.form.get('destination', '').strip()
        reason = request.form.get('reason', '').strip()

        if not destination or not reason:
            flash('All fields are required.', 'error')
        else:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO migration_requests (student_id, destination, reason) VALUES (?, ?, ?)",
                    (student['id'], destination, reason)
                )
                conn.commit()
                cursor.close()
                conn.close()
                flash('Migration certificate application submitted!', 'success')
                return redirect(url_for('student_migration'))

    return render_template('student_migration.html',
        student=student,
        active_page='migration',
        existing_request=existing_request
    )


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
