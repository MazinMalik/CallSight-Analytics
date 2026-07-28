import sqlite3
conn = sqlite3.connect('data/telecaller.db')
cursor = conn.cursor()
cursor.execute("SELECT id, transcript FROM calls ORDER BY created_at DESC LIMIT 1;")
res = cursor.fetchone()
if res:
    print(f"ID: {res[0]}\nTranscript: {res[1]}")
else:
    print("No rows found")
