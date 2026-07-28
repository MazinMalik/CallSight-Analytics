import sqlite3

text = "नमस्ते सर मैं श्रे बात कर रही हूँ यार हमारी कंपनी करती है जैसे"
conn = sqlite3.connect('data/telecaller.db')
cursor = conn.cursor()
cursor.execute("UPDATE calls SET transcript=? WHERE id='210e9367-abe8-4f03-8791-1e090b18a49f'", (text,))
conn.commit()
conn.close()
print("Updated successfully")
