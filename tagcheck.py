import os
import sqlite3
conn = sqlite3.connect(os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')))
cursor = conn.cursor()
result = cursor.execute("SELECT * FROM scba_units WHERE tag_number = 'SCBA-0001'").fetchone()
print(result)
