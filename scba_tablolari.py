import sqlite3
import os

DATABASE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db'))
print("Bağlanılan veritabanı:", os.path.abspath(DATABASE))

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# 🔧 cylinders tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS cylinders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT NOT NULL UNIQUE,
    capacity TEXT,
    pressure TEXT,
    last_refill_date TEXT,
    hydro_test_date TEXT,
    status TEXT,
    remarks TEXT
)
''')

# 🔧 regulators tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS regulators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT NOT NULL UNIQUE,
    brand TEXT,
    model TEXT,
    status TEXT,
    remarks TEXT
)
''')

# 🔧 scba_assemblies tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS scba_assemblies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cylinder_id INTEGER,
    regulator_id INTEGER,
    assigned_date TEXT,
    location TEXT,
    status TEXT,
    FOREIGN KEY (cylinder_id) REFERENCES cylinders(id),
    FOREIGN KEY (regulator_id) REFERENCES regulators(id)
)
''')

# 🔧 scba_inspections tablosu (zaten var ama garantiye alıyoruz)
cursor.execute('''
CREATE TABLE IF NOT EXISTS scba_inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scba_id INTEGER,
    inspection_date TEXT,
    inspected_by TEXT,
    pressure_check TEXT,
    ldv_leak_test TEXT,
    mask_leak_test TEXT,
    whistle_test TEXT,
    overall_condition TEXT,
    remarks TEXT,
    FOREIGN KEY (scba_id) REFERENCES scba_assemblies(id)
)
''')

conn.commit()
conn.close()

print("✅ Tüm SCBA tabloları hazır.")
