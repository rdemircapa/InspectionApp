#from app import login_required
from flask import session, redirect, url_for, flash
from auth_utils import login_required, role_required
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os




area_gas_monitor_bp = Blueprint('area_gas_monitor', __name__, template_folder='templates')

DB_FILE = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db'))

from flask import Blueprint, render_template
import sqlite3


@area_gas_monitor_bp.app_template_filter('todatetime')
def todatetime(value):
    from datetime import datetime
    return datetime.fromisoformat(value) if value else None





###### Area Gas Monitor List fonksiyonu

@area_gas_monitor_bp.route('/area-gas-monitors')
@login_required
@role_required('admin', 'inspector')
def list_area_gas_monitors():
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    rows = cursor.execute("SELECT * FROM area_gas_monitors").fetchall()

    # Statü bazlı sayılar
    active_count = cursor.execute(
        "SELECT COUNT(*) FROM area_gas_monitors WHERE status = 'Active'"
    ).fetchone()[0]
    inactive_count = cursor.execute(
        "SELECT COUNT(*) FROM area_gas_monitors WHERE status = 'Inactive'"
    ).fetchone()[0]
    service_count = cursor.execute(
        "SELECT COUNT(*) FROM area_gas_monitors WHERE status = 'Service'"
    ).fetchone()[0]

    conn.close()

    now = datetime.now()
    monitors = []
    calibration_soon_count = 0  # ⏳ 15 gün kala + geçmiş olanlar

    for r in rows:
        m = dict(r)
        due_status = "normal"
        days_left = None

        due_val = m.get('due_date')
        if due_val and str(due_val).strip() not in ("", "None"):
            parsed = None
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    parsed = datetime.strptime(str(due_val), fmt)
                    break
                except ValueError:
                    continue

            if parsed:
                days_left = (parsed.date() - now.date()).days

                # Tablo rengi: 15 gün veya daha az kaldıysa kırmızı (geçmişler dahil)
                if days_left <= 15:
                    due_status = "critical"
                    calibration_soon_count += 1  # 👈 geçmiş olanlar da dahil

        m['due_status'] = due_status
        m['days_left'] = days_left
        monitors.append(m)

    return render_template(
        'area_gas_monitor/list.html',
        monitors=monitors,
        active_count=active_count,
        inactive_count=inactive_count,
        service_count=service_count,
        calibration_soon_count=calibration_soon_count,
        current_time=now
    )



### MAP all monitors
@area_gas_monitor_bp.route('/map/area-gas-monitors')
@login_required
@role_required('admin', 'inspector')
def map_all_area_gas_monitors():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tag_number, model, location, sub_location, latitude, longitude
        FROM area_gas_monitors
        WHERE status = 'Active'
          AND latitude IS NOT NULL AND longitude IS NOT NULL
          AND latitude != '' AND longitude != ''
    """)
    rows = cursor.fetchall()
    conn.close()

    devices = []
    for row in rows:
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            devices.append({
                'tag_number': row['tag_number'],
                'model': row['model'] or 'N/A',
                'location': row['location'] or 'N/A',
                'sub_location': row['sub_location'] or 'N/A',
                'latitude': lat,
                'longitude': lon
            })
        except (ValueError, TypeError):
            continue

    return render_template("area_gas_monitor/map_all_area_gas_monitors.html", devices=devices)


### all monitors MAP END

###map single monitor
@area_gas_monitor_bp.route('/map/single/<tag>')
@login_required
@role_required('admin', 'inspector')
def view_single_area_gas_monitor(tag):
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Büyük/küçük harf duyarsız şekilde tag_number eşleştirme
    monitor = cursor.execute(
        "SELECT * FROM area_gas_monitors WHERE LOWER(tag_number) = LOWER(?)", (tag,)
    ).fetchone()
    conn.close()

    # Eşleşme bulunamadıysa listeye yönlendir
    if not monitor:
        flash("Device not found", "danger")
        return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))

    # Koordinatları float'a çevir
    try:
        lat = float(monitor['latitude'])
        lon = float(monitor['longitude'])
    except (ValueError, TypeError):
        flash("Invalid coordinates", "danger")
        return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))

    # .get() yerine doğrudan [] ile erişim ve boşluk kontrolü yap
    return render_template(
        "area_gas_monitor/map_single_area_gas_monitor.html",
        tag_number=monitor['tag_number'],
        model=monitor['model'] if monitor['model'] else 'N/A',
        location=monitor['location'] if monitor['location'] else 'N/A',
        sub_location=monitor['sub_location'] if monitor['sub_location'] else 'N/A',
        latitude=lat,
        longitude=lon
    )


#map single monitor end




# Listeleme
# @area_gas_monitor_bp.route('/gas/area', methods=['GET'])
# def list_area_gas_monitors():
 #    conn = sqlite3.connect(DB_FILE)
   #  conn.row_factory = sqlite3.Row
   #  monitors = conn.execute('SELECT * FROM area_gas_monitors').fetchall()
    # conn.close()
    # return render_template('area_gas_monitor/list.html', monitors=monitors)

# Ekleme
@area_gas_monitor_bp.route('/gas/area/add', methods=['GET', 'POST'])
def add_area_gas_monitor():
    tag_number_from_url = request.args.get('tag_number', '').strip().upper()  # GET ile gelen tag_number
    form_data = {
        'tag_number': tag_number_from_url or '',
        'serial_number': '',
        'sensor_serial_number': '',
        'location': '',
        'sub_location': '',
        'model': '',
        'gas_type': '',
        'calibration_date': '',
        'due_date': '',
        'status': '',
        'remarks': ''
    }

    if request.method == 'POST':
        # Formdan gelen veriler
        for key in form_data:
            form_data[key] = request.form.get(key, '').strip()

        tag_number = form_data['tag_number'].upper()

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        existing = cursor.execute("SELECT * FROM area_gas_monitors WHERE tag_number = ?", (tag_number,)).fetchone()

        try:
            if existing:
                if not existing['serial_number'] and not existing['sensor_serial_number'] and not existing['model']:
                    # Eksik ön-kayıt varsa → güncelle
                    cursor.execute("""
                        UPDATE area_gas_monitors
                        SET serial_number = ?, sensor_serial_number = ?, location = ?, sub_location = ?,
                            model = ?, gas_type = ?, calibration_date = ?, due_date = ?,
                            status = ?, remarks = ?
                        WHERE tag_number = ?
                    """, (
                        form_data['serial_number'], form_data['sensor_serial_number'],
                        form_data['location'], form_data['sub_location'],
                        form_data['model'], form_data['gas_type'],
                        form_data['calibration_date'], form_data['due_date'],
                        form_data['status'], form_data['remarks'],
                        tag_number
                    ))
                    flash(f"✅ Monitor '{tag_number}' was pre-created and is now completed.", "success")
                else:
                    flash(f"❌ Tag '{tag_number}' already exists and is in use.", "danger")
                    conn.close()
                    return render_template('area_gas_monitor/add.html', **form_data)

            else:
                # Tamamen yeni kayıt
                cursor.execute("""
                    INSERT INTO area_gas_monitors (
                        tag_number, serial_number, sensor_serial_number, location, sub_location,
                        model, gas_type, calibration_date, due_date, status, remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tag_number, form_data['serial_number'], form_data['sensor_serial_number'],
                    form_data['location'], form_data['sub_location'],
                    form_data['model'], form_data['gas_type'],
                    form_data['calibration_date'], form_data['due_date'],
                    form_data['status'], form_data['remarks']
                ))
                flash(f"✅ New area gas monitor '{tag_number}' added successfully.", "success")

            conn.commit()
            conn.close()
            return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))

        except sqlite3.IntegrityError:
            conn.close()
            flash("❌ Integrity error occurred. Possible duplicate tag.", "danger")
            return render_template('area_gas_monitor/add.html', **form_data)

    # GET request – form boş veya otomatik tag_number dolu
    return render_template('area_gas_monitor/add.html', **form_data)




# Güncelleme
@area_gas_monitor_bp.route('/gas/area/edit/<int:id>', methods=['GET', 'POST'])
def edit_area_gas_monitor(id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    monitor = cursor.execute('SELECT * FROM area_gas_monitors WHERE id = ?', (id,)).fetchone()
    if not monitor:
        conn.close()
        flash("❌ Monitor not found.", "danger")
        return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))

    # GET verilerini form_data'ya yükle
    form_data = {
        'tag_number': monitor['tag_number'] or '',
        'serial_number': monitor['serial_number'] or '',
        'sensor_serial_number': monitor['sensor_serial_number'] or '',
        'location': monitor['location'] or '',
        'sub_location': monitor['sub_location'] or '',
        'model': monitor['model'] or '',
        'gas_type': monitor['gas_type'] or '',
        'calibration_date': monitor['calibration_date'] or '',
        'due_date': monitor['due_date'] or '',
        'status': monitor['status'] or '',
        'remarks': monitor['remarks'] or ''
    }

    if request.method == 'POST':
        # Formdan gelen veriler
        for key in form_data:
            form_data[key] = request.form.get(key, '').strip()

        try:
            cursor.execute("""
                UPDATE area_gas_monitors SET
                    tag_number = ?, serial_number = ?, sensor_serial_number = ?,
                    location = ?, sub_location = ?, model = ?, gas_type = ?,
                    calibration_date = ?, due_date = ?, status = ?, remarks = ?
                WHERE id = ?
            """, (
                form_data['tag_number'].upper(),  # normalize edilebilir
                form_data['serial_number'],
                form_data['sensor_serial_number'],
                form_data['location'],
                form_data['sub_location'],
                form_data['model'],
                form_data['gas_type'],
                form_data['calibration_date'],
                form_data['due_date'],
                form_data['status'],
                form_data['remarks'],
                id
            ))
            conn.commit()
            conn.close()
            flash(f"✅ Monitor '{form_data['tag_number']}' updated successfully.", "success")
            return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))

        except sqlite3.IntegrityError:
            conn.close()
            flash("❌ Integrity error occurred. Possible duplicate tag.", "danger")
            return render_template('area_gas_monitor/edit.html', monitor=form_data)

    conn.close()
    return render_template('area_gas_monitor/edit.html', monitor=form_data)



# Silme
@area_gas_monitor_bp.route('/gas/area/delete/<int:id>', methods=['GET'])
def delete_area_gas_monitor(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM area_gas_monitors WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Area Gas Monitor deleted successfully.', 'success')
    return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))


# MANUAL QR SCAN ROUTE
@area_gas_monitor_bp.route('/gas/area/manual-scan', methods=['GET', 'POST'])
def manual_scan_area_monitor():
    if request.method == 'POST':
        tag_number = request.form.get('tag_number')

        # Veritabanını kontrol et
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        monitor = cursor.execute("SELECT * FROM area_gas_monitors WHERE tag_number = ?", (tag_number,)).fetchone()
        conn.close()

        if monitor:
            return redirect(url_for('area_gas_monitor.inspect_area_monitor', tag_number=tag_number))
        else:
            # Eğer kayıt yoksa, ekleme formuna yönlendir
            return redirect(url_for('area_gas_monitor.add_area_gas_monitor', tag_number=tag_number))

    return render_template('area_gas_monitor/manual_scan.html')



from datetime import datetime

@area_gas_monitor_bp.route('/gas/area/inspect/<tag_number>', methods=['GET', 'POST'])
def inspect_area_monitor(tag_number):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    monitor = cursor.execute("SELECT * FROM area_gas_monitors WHERE tag_number = ?", (tag_number,)).fetchone()

    if not monitor:
        conn.close()
        flash("Monitor not found.", "danger")
        return redirect(url_for('area_gas_monitor.manual_scan_area_monitor'))

    if request.method == 'POST':
        sub_location = request.form.get('sub_location')
        remarks = request.form.get('remarks')
        status = request.form.get('status')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # Status "Active" ise activated_at zamanı ata, değilse NULL yap
        if status == "Active":
            activated_at = datetime.now().isoformat()
        else:
            activated_at = None

        cursor.execute("""
            UPDATE area_gas_monitors
            SET sub_location = ?, remarks = ?, status = ?, latitude = ?, longitude = ?, activated_at = ?
            WHERE tag_number = ?
        """, (sub_location, remarks, status, latitude, longitude, activated_at, tag_number))

        conn.commit()
        conn.close()
        flash("Monitor info updated successfully.", "success")
        return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))

    conn.close()
    return render_template('area_gas_monitor/inspect.html', monitor=monitor)




############## aktif sure hesaplama
@area_gas_monitor_bp.route('/area-gas-monitor/status/<int:id>/<string:new_status>')
@login_required
@role_required('admin', 'inspector')
def update_status(id, new_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if new_status == "Active":
        from datetime import datetime
        activated_at = datetime.now().isoformat()
        cursor.execute("""
            UPDATE area_gas_monitors
            SET status = ?, activated_at = ?
            WHERE id = ?
        """, (new_status, activated_at, id))
    else:
        cursor.execute("""
            UPDATE area_gas_monitors
            SET status = ?, activated_at = NULL
            WHERE id = ?
        """, (new_status, id))

    conn.commit()
    conn.close()
    flash(f"Status updated to {new_status}", "success")
    return redirect(url_for('area_gas_monitor.list_area_gas_monitors'))



############## aktif sure hesaplama

### Kart Filitreleme
@area_gas_monitor_bp.route('/area-gas-monitors/filter/<filter_type>')
@login_required
@role_required('admin', 'inspector')
def filter_area_gas_monitors(filter_type):
    import sqlite3
    from datetime import datetime

    now = datetime.now()

    def enrich_rows(rows):
        """due_status (normal/critical) ve days_left ekle"""
        monitors = []
        for r in rows:
            m = dict(r)
            due_status = "normal"
            days_left = None
            due_val = m.get('due_date')
            if due_val and str(due_val).strip() not in ("", "None"):
                parsed = None
                for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y"):
                    try:
                        parsed = datetime.strptime(str(due_val), fmt)
                        break
                    except ValueError:
                        continue
                if parsed:
                    days_left = (parsed.date() - now.date()).days
                    if days_left <= 15:
                        due_status = "critical"
            m['due_status'] = due_status
            m['days_left'] = days_left
            monitors.append(m)
        return monitors

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Status tabanlı filtreler SQL ile
    if filter_type in ("active", "inactive", "service"):
        status_map = {
            "active": "Active",
            "inactive": "Inactive",
            "service": "Service",
        }
        rows = cursor.execute(
            "SELECT * FROM area_gas_monitors WHERE status = ?",
            (status_map[filter_type],)
        ).fetchall()
        conn.close()
        monitors = enrich_rows(rows)
        return render_template(
            'area_gas_monitor/list_filtered.html',
            monitors=monitors,
            filter_type=filter_type,
            current_time=now  # ✅ ŞABLONA GÖNDER
        )

    # Kalibrasyon kritik: (<=15 gün KALAN + geçmiş)
    if filter_type == "calibration_soon":
        rows = cursor.execute("SELECT * FROM area_gas_monitors").fetchall()
        conn.close()
        all_monitors = enrich_rows(rows)
        monitors = [m for m in all_monitors if m['days_left'] is not None and m['days_left'] <= 15]
        return render_template(
            'area_gas_monitor/list_filtered.html',
            monitors=monitors,
            filter_type=filter_type,
            current_time=now  # ✅ ŞABLONA GÖNDER
        )

    # Bilinmeyen filtre: hepsini göster (ya da 404 dönebilirsin)
    rows = cursor.execute("SELECT * FROM area_gas_monitors").fetchall()
    conn.close()
    monitors = enrich_rows(rows)
    return render_template(
        'area_gas_monitor/list_filtered.html',
        monitors=monitors,
        filter_type=filter_type,
        current_time=now  # ✅ ŞABLONA GÖNDER
    )


### Kart Filitreleme son






























