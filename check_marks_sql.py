import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE name='marks';")
sql = cursor.fetchone()[0]
print(sql)

conn.close()
