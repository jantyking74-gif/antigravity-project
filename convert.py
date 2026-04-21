import re

with open('app.py', 'r') as f:
    code = f.read()

# Replace imports
code = code.replace('import mysql.connector', 'import sqlite3')

# Update get_db_connection
old_conn_func = '''def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=active_config.MYSQL_HOST,
            user=active_config.MYSQL_USER,
            password=active_config.MYSQL_PASSWORD,
            database=active_config.MYSQL_DATABASE,
            port=active_config.MYSQL_PORT,
            autocommit=True  # Ensure changes are saved immediately
        )
        return connection
    except Exception as e:
        print(f"CRITICAL: Database connection failed! {e}")
        return None'''

new_conn_func = '''def get_db_connection():
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"CRITICAL: Database connection failed! {e}")
        return None'''
code = code.replace(old_conn_func, new_conn_func)

# Fix init_db definitions
code = code.replace('INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
code = code.replace('UNIQUE KEY unique_student_subject (student_id, subject)', 'UNIQUE(student_id, subject)')
code = code.replace('UNIQUE KEY unique_student_semester_form (student_id, semester)', 'UNIQUE(student_id, semester)')
code = code.replace('INT DEFAULT 1', 'INTEGER DEFAULT 1')
code = code.replace('INT NOT NULL', 'INTEGER NOT NULL')

# Fix add columns (ALTER TABLE in SQLite can be picky, but ADD COLUMN is supported)
# Wrap the exception correctly
code = code.replace('except mysql.connector.Error as e:', 'except sqlite3.Error as e:')
code = code.replace('except mysql.connector.Error:', 'except sqlite3.Error:')
code = code.replace('except mysql.connector.Error', 'except sqlite3.Error')

# Replace MySQL duplicate entry error handling
code = code.replace('e.errno == 1062', '"UNIQUE constraint failed" in str(e)')

# Remove cursor dictionary=True 
code = code.replace('cursor = conn.cursor(dictionary=True)', 'cursor = conn.cursor()')

# Parameter binding: replace %s with ?
# We use regex to replace %s that are not within format strings or other literals,
# But since this is a simple script and %s is only used for sql parameters here:
code = code.replace('%s', '?')

# cursor.lastrowid is identical in sqlite3

with open('app.py', 'w') as f:
    f.write(code)

print("Conversion complete!")
