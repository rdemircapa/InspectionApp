import sqlite3
import os

# Veritabanı yolu
DATABASE = '/home/mytestapp/mysite/database.db'
print("🔧 Bağlanılıyor:", os.path.abspath(DATABASE))

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Cylinder verilerini aktar
cursor.execute("""
INSERT OR IGNORE INTO cylinders (serial_number, capacity, pressure, status)
SELECT cylinder_serial, cylinder_capacity, cylinder_pressure, 'Active'
FROM scba_units
WHERE cylinder_serial IS NOT NULL AND TRIM(cylinder_serial) != ''
""")

print("✅ scba_units → cylinders aktarımı tamamlandı.")

# Regulator verilerini aktar
cursor.execute("""
INSERT OR IGNORE INTO regulators (serial_number, brand, model, status)
SELECT regulator_serial, brand, model, 'Active'
FROM scba_units
WHERE regulator_serial IS NOT NULL AND TRIM(regulator_serial) != ''
""")

print("✅ scba_units → regulators aktarımı tamamlandı.")

conn.commit()
conn.close()
print("🚀 İşlem tamamlandı.")
