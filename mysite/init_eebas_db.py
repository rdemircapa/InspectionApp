#!/usr/bin/env python3
"""
EEBA/SCBA ekipman tablosu için SQLite veritabanı oluşturucu
- Tablo: eebas
- Indeksler: tag_no (unique), location+sub_location, due date alanları
- Trigger: UPDATE'ta updated_at alanını otomatik günceller
"""

import sqlite3
from pathlib import Path

# --- Ayarlar ---
DB_PATH = Path("/home/mytestapp/mysite/database.db")  # gerekirse değiştir
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DDL_TABLE = """
CREATE TABLE IF NOT EXISTS eebas (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    responsible           TEXT,            -- RESPONSIBLE
    make_brand            TEXT,            -- MAKE / BRAND
    cyl_no                TEXT,            -- CYL.NO.
    capacity              TEXT,            -- CAPACITY (örn: "15 MINS EEBA")
    tag_no                TEXT NOT NULL,   -- TAG NO. (QR/TAG)
    location              TEXT,            -- LOCATION (örn: GOP)
    sub_location          TEXT,            -- SUB LOCATION (örn: Room 55)

    -- Hydrostatic test
    hyd_ins_date          TEXT,            -- 'YYYY-MM-DD'
    hyd_due_date          TEXT,

    -- Refilling
    refilling_filled_date TEXT,
    refilling_due_date    TEXT,

    -- Monthly inspections
    monthly_ins_date      TEXT,
    monthly_due_date      TEXT,

    -- Visual inspection
    mask_status           TEXT,            -- 'OK' / 'FAIL' (istersen BOOLEAN’a çevirebiliriz)
    cyl_pressure_bar      REAL,            -- örn: 200
    straps_status         TEXT,            -- 'OK' / 'FAIL'
    bag_status            TEXT,            -- 'OK' / 'FAIL'
    overall_condition     TEXT,            -- 'SATISFACTORY' / 'UNSATISFACTORY' vb.

    inspected_by          TEXT,
    remarks               TEXT,
    corrective_action     TEXT,

    is_active             INTEGER NOT NULL DEFAULT 1,  -- 1=aktif, 0=pasif
    created_at            TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at            TEXT NOT NULL DEFAULT (datetime('now')),

    -- Basit doğrulamalar
    CONSTRAINT uq_tag_no UNIQUE (tag_no),
    CONSTRAINT chk_pressure_nonneg CHECK (cyl_pressure_bar IS NULL OR cyl_pressure_bar >= 0)
);
"""

DDL_INDEXES = [
    # Tekrarlı çalıştırmaya uygun: IF NOT EXISTS
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_eebas_tag_no ON eebas(tag_no);",
    "CREATE INDEX IF NOT EXISTS idx_eebas_location_sub ON eebas(location, sub_location);",
    "CREATE INDEX IF NOT EXISTS idx_eebas_due_dates ON eebas(hyd_due_date, refilling_due_date, monthly_due_date);",
]

DDL_TRIGGER_DROP_IF_EXISTS = """
-- SQLite CREATE TRIGGER IF NOT EXISTS bazı sürümlerde yok; güvenli olmak için önce varsa siliyoruz
DROP TRIGGER IF EXISTS trg_eebas_updated_at;
"""

DDL_TRIGGER_CREATE = """
CREATE TRIGGER trg_eebas_updated_at
AFTER UPDATE ON eebas
FOR EACH ROW
BEGIN
    UPDATE eebas SET updated_at = datetime('now') WHERE id = NEW.id;
END;
"""

def init_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")   # eşzamanlı okuma/yazma için daha güvenli
        conn.execute("PRAGMA synchronous = NORMAL;")

        # Tablo
        conn.execute(DDL_TABLE)

        # Indeksler
        for stmt in DDL_INDEXES:
            conn.execute(stmt)

        # Trigger (önce eskiyi düşür, sonra oluştur)
        conn.executescript(DDL_TRIGGER_DROP_IF_EXISTS)
        conn.executescript(DDL_TRIGGER_CREATE)

        conn.commit()
        print(f"OK: Veritabanı hazır -> {db_path}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db(DB_PATH)

    # İsteğe bağlı: küçük bir örnek kayıt (yorum satırından çıkarıp test edebilirsin)
    """
    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.execute(
            \"\"\"INSERT INTO eebas
            (responsible, make_brand, cyl_no, capacity, tag_no, location, sub_location,
             hyd_ins_date, hyd_due_date,
             refilling_filled_date, refilling_due_date,
             monthly_ins_date, monthly_due_date,
             mask_status, cyl_pressure_bar, straps_status, bag_status, overall_condition,
             inspected_by, remarks, corrective_action)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)\"\"\",
            (
                "NPCC SAIPEM", "DRAGER", "YHG-171", "15 MINS EEBA", "JV-EEBD 001",
                "GOP", "Room 55",
                "2024-09-09", "2029-09-09",
                "2025-07-01", "2026-01-01",
                "2025-08-09", "2025-09-08",
                "OK", 200, "OK", "OK", "SATISFACTORY",
                "JV HSE & Al Masaood Technician", None, None
            )
        )
    conn.close()
    print("Örnek kayıt eklendi.")
    """
