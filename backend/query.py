import sqlite3
conn = sqlite3.connect('data/telecaller.db')
cursor = conn.cursor()
cursor.execute("SELECT id, error_message, transcript FROM calls ORDER BY created_at DESC LIMIT 1;")
res = cursor.fetchone()
print(res)
