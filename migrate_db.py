import sqlite3
import os

def migrate():
    db_path = 'database.db'
    if not os.path.exists(db_path):
        print("Database not found. Run app.py first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Checking marks table...")
    
    # 1. Check if semester column exists
    cursor.execute("PRAGMA table_info(marks)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'semester' not in columns:
        print("Adding semester column...")
        cursor.execute("ALTER TABLE marks ADD COLUMN semester INTEGER DEFAULT 1")
    
    # 2. Recreate table to fix UNIQUE constraint
    # We want UNIQUE(student_id, subject, semester)
    print("Updating UNIQUE constraint...")
    
    # Create temp table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marks_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject VARCHAR(100) NOT NULL,
        marks INTEGER NOT NULL,
        semester INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        UNIQUE(student_id, subject, semester)
    )
    ''')
    
    # Copy data (ignoring duplicates that might now exist if we were stricter before)
    # Actually, we are making it LESS strict (adding semester to unique), so no data loss.
    cursor.execute("INSERT INTO marks_new (id, student_id, subject, marks, semester, created_at) SELECT id, student_id, subject, marks, semester, created_at FROM marks")
    
    # Drop old table
    cursor.execute("DROP TABLE marks")
    
    # Rename new table
    cursor.execute("ALTER TABLE marks_new RENAME TO marks")
    
    conn.commit()
    conn.close()
    print("Migration successful!")

if __name__ == '__main__':
    migrate()
