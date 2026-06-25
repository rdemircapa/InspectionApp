import sqlite3
conn = sqlite3.connect('/home/mytestapp/mysite/database.db')
cursor = conn.cursor()
result = cursor.execute("SELECT * FROM scba_units WHERE tag_number = 'SCBA-0001'").fetchone()
print(result)
