import sqlite3

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = sqlite3.connect('database.db')
conn.row_factory = dict_factory
cursor = conn.cursor()

print("--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table['name'])

print("\n--- Admin ---")
cursor.execute("SELECT * FROM admin;")
admins = cursor.fetchall()
for admin in admins:
    print(admin)

print("\n--- Students (first 5) ---")
cursor.execute("SELECT * FROM students LIMIT 5;")
students = cursor.fetchall()
for student in students:
    print(student)

conn.close()
