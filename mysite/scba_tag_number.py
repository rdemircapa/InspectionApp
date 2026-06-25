import os
import sqlite3

DATABASE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db'))

def assign_scba_tags():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM scba_units WHERE tag_number IS NULL OR tag_number = '' ORDER BY id")
    rows = cursor.fetchall()

    for i, row in enumerate(rows, start=1):
        tag = f"SCBA-{i:04d}"
        cursor.execute("UPDATE scba_units SET tag_number = ? WHERE id = ?", (tag, row[0]))

    conn.commit()
    conn.close()
    print(f"✅ {len(rows)} SCBA units tagged successfully.")

assign_scba_tags()
