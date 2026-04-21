import sqlite3

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = sqlite3.connect('database.db')
conn.row_factory = dict_factory
cursor = conn.cursor()

cursor.execute("SELECT * FROM marks WHERE student_id = 1")
marks = cursor.fetchall()
print(f"Marks for student 1: {marks}")

conn.close()
