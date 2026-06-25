from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from auth_utils import login_required, role_required
from datetime import datetime, timedelta, date
import sqlite3
import os

# --- Ortak Ayarlar ---
from . import personal_gas_monitor_bp

DB_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db'))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Yardımcılar
def to_date(s: str):
    """'YYYY-MM-DD' -> date | None"""
    try:
        return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except Exception:
        return None

def to_iso(d: date):
    """date -> 'YYYY-MM-DD' | None"""
    return d.strftime("%Y-%m-%d") if d else None

# =========================
#   ADD
# =========================
@personal_gas_monitor_bp.route('/gas/personal/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector', 'viewer')  # sadece bu roller erişebilir
def add_personal_gas_monitor():
    if request.method == 'POST':
        serial_number   = (request.form.get('serial_number') or '').strip()
        model           = (request.form.get('model') or '').strip()
        manufacturer    = (request.form.get('manufacturer') or '').strip()
        calibration_raw = (request.form.get('calibration_date') or '').strip()
        status          = (request.form.get('status') or '').strip()
        location        = (request.form.get('location') or '').strip()

        # OPSIYONEL alanlar
        assigned_to         = (request.form.get('assigned_to') or '').strip() or None
        assigned_user_name  = (request.form.get('assigned_user_name') or '').strip() or None
        assigned_date_raw   = (request.form.get('assigned_date') or '').strip()
        remarks             = (request.form.get('remarks') or '').strip() or None

        # Yeni alanlar
        bump_test_raw   = (request.form.get('bump_test_date') or '').strip()
        bump_status     = (request.form.get('bump_status') or '').strip() or None

        # Tarihleri dönüştür
        calibration_date     = to_date(calibration_raw)
        assigned_date        = to_date(assigned_date_raw)
        bump_test_date       = to_date(bump_test_raw)

        # Backend'de due date hesapla (+180 gün)
        calibration_due_date = to_iso(calibration_date + timedelta(days=180)) if calibration_date else None

        # DB'ye 'YYYY-MM-DD' formatında yazalım (SQLite TEXT/DATE uyumlu)
        calibration_date_str = to_iso(calibration_date)
        assigned_date_str    = to_iso(assigned_date)
        bump_test_date_str   = to_iso(bump_test_date)

        # Küçük doğrulama (opsiyonel): Pass/Fail seçiliyse tarih istenir
        if bump_status in ('Pass', 'Fail') and not bump_test_date_str:
            flash('Please provide a Bump Test Date when status is Pass/Fail.', 'warning')
            return render_template('personal_gas_monitor/add.html')

        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO personal_gas_monitors (
                    serial_number, model, manufacturer,
                    calibration_date, calibration_due_date,
                    status, location,
                    assigned_to, assigned_user_name, assigned_date,
                    bump_test_date, bump_status,
                    remarks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                serial_number, model, manufacturer,
                calibration_date_str, calibration_due_date,
                status, location,
                assigned_to, assigned_user_name, assigned_date_str,
                bump_test_date_str, bump_status,
                remarks
            ))
            conn.commit()
            flash('Personal Gas Monitor added successfully!', 'success')
        except sqlite3.IntegrityError as e:
            # Örn: unique(serial_number) ihlali vb.
            flash(f'Error: {str(e)}', 'danger')
        finally:
            conn.close()

        return redirect(url_for('personal_gas_monitor.list_personal_gas_monitor'))

    return render_template('personal_gas_monitor/add.html')


# =========================
#   EDIT
# =========================
@personal_gas_monitor_bp.route('/gas/personal/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def edit_personal_gas_monitor(id):
    conn = get_db_connection()
    monitor = conn.execute("SELECT * FROM personal_gas_monitors WHERE id = ?", (id,)).fetchone()

    if not monitor:
        conn.close()
        flash("Monitor not found.", "danger")
        return redirect(url_for('personal_gas_monitor.list_personal_gas_monitor'))

    if request.method == 'POST':
        serial_number   = (request.form.get('serial_number') or '').strip()
        model           = (request.form.get('model') or '').strip()
        manufacturer    = (request.form.get('manufacturer') or '').strip()
        calibration_raw = (request.form.get('calibration_date') or '').strip()
        status          = (request.form.get('status') or '').strip()
        location        = (request.form.get('location') or '').strip()

        # OPSIYONEL alanlar
        assigned_to         = (request.form.get('assigned_to') or '').strip() or None
        assigned_user_name  = (request.form.get('assigned_user_name') or '').strip() or None
        assigned_date_raw   = (request.form.get('assigned_date') or '').strip()
        remarks             = (request.form.get('remarks') or '').strip() or None

        # Yeni alanlar
        bump_test_raw   = (request.form.get('bump_test_date') or '').strip()
        bump_status     = (request.form.get('bump_status') or '').strip() or None

        # Tarihler
        calibration_date     = to_date(calibration_raw)
        assigned_date        = to_date(assigned_date_raw)
        bump_test_date       = to_date(bump_test_raw)

        # Due date yeniden hesapla
        calibration_due_date = to_iso(calibration_date + timedelta(days=180)) if calibration_date else None

        calibration_date_str = to_iso(calibration_date)
        assigned_date_str    = to_iso(assigned_date)
        bump_test_date_str   = to_iso(bump_test_date)

        # Pass/Fail ise bump tarihi iste (opsiyonel kural)
        if bump_status in ('Pass', 'Fail') and not bump_test_date_str:
            conn.close()
            flash('Please provide a Bump Test Date when status is Pass/Fail.', 'warning')
            return render_template('personal_gas_monitor/edit.html', monitor=monitor)

        conn.execute("""
            UPDATE personal_gas_monitors SET
                serial_number = ?,
                model = ?,
                manufacturer = ?,
                calibration_date = ?,
                calibration_due_date = ?,
                status = ?,
                location = ?,
                assigned_to = ?,
                assigned_user_name = ?,
                assigned_date = ?,
                bump_test_date = ?,
                bump_status = ?,
                remarks = ?
            WHERE id = ?
        """, (
            serial_number,
            model,
            manufacturer,
            calibration_date_str,
            calibration_due_date,
            status,
            location,
            assigned_to,
            assigned_user_name,
            assigned_date_str,
            bump_test_date_str,
            bump_status,
            remarks,
            id
        ))
        conn.commit()
        conn.close()
        flash('Monitor updated successfully.', 'success')
        return redirect(url_for('personal_gas_monitor.list_personal_gas_monitor'))

    conn.close()
    return render_template('personal_gas_monitor/edit.html', monitor=monitor)


# =========================
#   DELETE (değişmedi)
# =========================
@personal_gas_monitor_bp.route('/gas/personal/delete/<int:id>')
@login_required
@role_required('admin')  # sadece bu roller erişebilir
def delete_personal_gas_monitor(id):
    conn = get_db_connection()
    monitor = conn.execute("SELECT * FROM personal_gas_monitors WHERE id = ?", (id,)).fetchone()
    if monitor:
        conn.execute("DELETE FROM personal_gas_monitors WHERE id = ?", (id,))
        conn.commit()
        flash('Monitor deleted successfully.', 'success')
    else:
        flash('Monitor not found.', 'danger')
    conn.close()
    return redirect(url_for('personal_gas_monitor.list_personal_gas_monitor'))


# =========================
#   GET NAME (değişmedi)
# =========================
@personal_gas_monitor_bp.route('/get-user-name')
def get_user_name():
    badge = request.args.get('badge', '')
    conn = get_db_connection()
    user = conn.execute("SELECT full_name FROM users WHERE badge_number = ?", (badge,)).fetchone()
    conn.close()
    if user:
        return jsonify({'name': user['full_name']})
    else:
        return jsonify({'name': None})


# =========================
#   LIST
# =========================
@personal_gas_monitor_bp.route('/gas/personal')
@login_required
@role_required('admin', 'inspector', 'viewer')  # sadece bu roller erişebilir
def list_personal_gas_monitor():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM personal_gas_monitors").fetchall()
    conn.close()

    monitors = []
    calibration_due_count = 0
    today = date.today()

    for row in rows:
        cal_date_str = row['calibration_date']
        due_date_str = row['calibration_due_date']

        cal_date = to_date(cal_date_str)
        due_date = to_date(due_date_str) or (cal_date + timedelta(days=180) if cal_date else None)

        remaining = None
        if due_date:
            remaining = (due_date - today).days
            if remaining <= 15:
                calibration_due_count += 1

        monitors.append({
            'id': row['id'],
            'serial_number': row['serial_number'],
            'model': row['model'],
            'manufacturer': row['manufacturer'],
            'calibration_date': cal_date_str,
            'calibration_due_date': to_iso(due_date) if due_date else None,
            'status': row['status'],
            'location': row['location'],
            'assigned_to': row['assigned_to'],
            'assigned_user_name': row.get('assigned_user_name') if isinstance(row, dict) else row['assigned_user_name'] if 'assigned_user_name' in row.keys() else None,
            'assigned_date': row['assigned_date'],
            'bump_test_date': row['bump_test_date'] if 'bump_test_date' in row.keys() else None,
            'bump_status': row['bump_status'] if 'bump_status' in row.keys() else None,
            'remarks': row['remarks'],
            'remaining_days': remaining
        })

    total_monitors = len(monitors)

    return render_template(
        "personal_gas_monitor/list.html",
        monitors=monitors,
        total_monitors=total_monitors,
        calibration_due_count=calibration_due_count
    )
