from flask import Flask, render_template, session, request, redirect, url_for, g, flash, send_file
from auth_utils import login_required, role_required
import os


app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your_super_secret_key_12345')
import sqlite3
import pandas as pd
from datetime import datetime, date
from io import BytesIO
import qrcode
from functools import wraps
from datetime import datetime, timedelta
from area_gas_monitor.routes import area_gas_monitor_bp
#from area_gas_monitor import area_gas_monitor_bp
from new_module.routes import new_module_bp  # doğru import
from personal_gas_monitor import personal_gas_monitor_bp
from eeba.routes import eeba_bp
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Image
from reportlab.lib.utils import ImageReader
from flask import jsonify


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, 'database.db'))
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', os.path.join(BASE_DIR, 'output'))

# klasör yoksa oluştur
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


#@role_required('admin')                       # sadece admin
#@role_required('admin', 'inspector')          # admin ve inspector
#@role_required('admin', 'inspector', 'viewer')# hepsi erişebilir



app.register_blueprint(eeba_bp)
app.register_blueprint(area_gas_monitor_bp)
app.register_blueprint(new_module_bp)        # doğru kayıt
app.register_blueprint(personal_gas_monitor_bp)


@app.template_filter('todatetime')
def todatetime(value):
    from datetime import datetime
    return datetime.fromisoformat(value) if value else None





#DATABASE = 'database.db'

DATABASE = DB_FILE  # tek kaynak

from functools import wraps
from flask import session, redirect, url_for, flash

def requires_roles(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = session.get('user')
            if not user:
                flash("Please log in first.", "warning")
                return redirect(url_for('login'))
            if user.get('role') not in roles:
                flash("Access denied. You do not have permission.", "danger")
                return redirect(url_for('home'))
            return func(*args, **kwargs)
        return wrapper
    return decorator








@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}








from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, password FROM auth_users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user[4]):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['full_name'] = user[2]
            session['role'] = user[3]
            flash(f"Welcome, {user[2]}!", "success")
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid badge number or password."

    return render_template("login.html", error=error)



@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

from functools import wraps
from flask import session, redirect, url_for, flash

#def login_required(f):
 #   @wraps(f)
  #  def decorated_function(*args, **kwargs):
   #     if 'user_id' not in session:
    #        flash("Please log in first.", "warning")
     #       return redirect(url_for('login'))
      #  return f(*args, **kwargs)
#    return decorated_function







from functools import wraps
from flask import session, redirect, url_for, flash

#def role_required(*roles):
 #   def wrapper(f):
  #      @wraps(f)
   #     def decorated_function(*args, **kwargs):
    #        if session.get('role') not in roles:
     #           flash("You don't have permission to access this page.", "danger")
      #          return redirect(url_for('dashboard'))
       #     return f(*args, **kwargs)
        #return decorated_function
#    return wrapper







# Jinja'da string'i date'e çevirmek için filtre
app.jinja_env.filters['to_datetime'] = lambda s, f: datetime.strptime(s, f)

from datetime import datetime

@app.template_filter('format_date_custom')
def format_date_custom(value):
    try:
        # Değer string olarak geliyorsa dönüştür
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d')
        return value.strftime('%d-%b-%Y').upper()  # 12-APR-2025
    except Exception as e:
        return value  # Tarih değilse orijinal değeri döndür


from datetime import datetime

def format_date_dd_mmm_yyyy(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%b-%Y').upper()
    except:
        return date_str  # geçersizse olduğu gibi döndür



def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Verileri dict gibi almak için
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/init-db')
def init_db():
   initialize_database()
   return "✅ Veritabanı başarıyla oluşturuldu."

def get_db_connection():
    import os
    print("📂 Aktif veritabanı dosyası:", os.path.abspath(DATABASE))
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 1. Brands
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # 2. Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            badge_number TEXT PRIMARY KEY,
            full_name TEXT NOT NULL
        )
    ''')

    # 3. Products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER,
            serial_id TEXT,
            name TEXT,
            quantity INTEGER,
            type TEXT,
            details TEXT,
            first_inspection_date TEXT,
            inspection_date TEXT,
            status TEXT,
            remarks TEXT,
            FOREIGN KEY (brand_id) REFERENCES brands (id)
        )
    ''')

    # 4. Inspections
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            inspection_date TEXT,
            inspected_by TEXT,
            inspection_result TEXT,
            notes TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 5. Assignments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            assigned_to TEXT,
            badge_number TEXT,
            assigned_date TEXT,
            return_date TEXT,
            notes TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 6. SCBA Units
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scba_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            cylinder_capacity TEXT,
            cylinder_pressure TEXT,
            refiling_date TEXT,
            hydro_test_date TEXT,
            cylinder_serial TEXT UNIQUE,
            regulator_serial TEXT,
            remarks TEXT,
            location TEXT
        )
    ''')

    # 7. SCBA Inspections
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
            FOREIGN KEY (scba_id) REFERENCES scba_units(id)
        )
    ''')

    # 8. Tag Cards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE,
            qr_url TEXT
        )
    ''')

    # 9. Fire Extinguishers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fire_extinguishers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            extinguisher_type TEXT,
            capacity TEXT,
            responsible_company_id INTEGER,
            tag_number TEXT,
            location TEXT,
            sub_location TEXT,
            third_party_inspection_date TEXT,
            third_party_due_date TEXT,
            monthly_inspection_date TEXT,
            monthly_due_date TEXT,
            pressure_gauge TEXT,
            hose_nozzle TEXT,
            safety_pin TEXT,
            trigger TEXT,
            overall_condition TEXT,
            remarks TEXT,
            FOREIGN KEY (responsible_company_id) REFERENCES companies(id)
        )
    ''')

    # 10. Companies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE NOT NULL
        )
    ''')

    # 11. Product Types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()



initialize_database()


@app.route('/get-name-by-badge')
def get_name_by_badge():
    badge = request.args.get('badge')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE badge_number = ?", (badge,))
    result = cursor.fetchone()
    conn.close()
    return {'name': result['full_name'] if result else ''}

@app.route('/delete-user/<badge_number>', methods=['POST'])
def delete_user(badge_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE badge_number = ?", (badge_number,))
    conn.commit()
    conn.close()
    flash(f"User with badge {badge_number} deleted.", "success")
    return redirect(url_for('add_user'))


@app.route('/delete-company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
    conn.commit()
    conn.close()
    flash("Company deleted successfully.", "success")
    return redirect(url_for('add_company'))



@app.route('/edit-user/<badge_number>', methods=['GET', 'POST'])
def edit_user(badge_number):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_name = request.form['full_name'].strip()
        cursor.execute("UPDATE users SET full_name = ? WHERE badge_number = ?", (new_name, badge_number))
        conn.commit()
        conn.close()
        flash("User updated successfully.", "success")
        return redirect(url_for('add_user'))

    user = cursor.execute("SELECT * FROM users WHERE badge_number = ?", (badge_number,)).fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

# SCBA TAG

import sqlite3

def generate_next_scba_tag():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Mevcut tüm tag_number kayıtlarını al
    cursor.execute("SELECT tag_number FROM scba_assemblies WHERE tag_number IS NOT NULL")
    tags = cursor.fetchall()
    conn.close()

    max_num = 0
    for tag in tags:
        if tag[0] and tag[0].startswith("SCBA-"):
            try:
                num = int(tag[0].split("-")[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue

    next_num = max_num + 1
    return f"SCBA-{next_num:04d}"  # Örnek: SCBA-0001


#SCBA ID Get
@app.route('/get-scba-id/<tag>')
def get_scba_id(tag):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM scba_units WHERE tag_number = ?", (tag,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {"id": row["id"]}
    else:
        return {"id": None}



#





def inspect_scba_logic(expected_cylinder_serial, expected_regulator_serial,
                       actual_cylinder_serial, actual_regulator_serial):
    import sqlite3
    conn = sqlite3.connect(DATABASE)  # tam yol kullanalım
    cursor = conn.cursor()

    # Hangi seri numaraları değişti?
    updated = (
        expected_cylinder_serial != actual_cylinder_serial or
        expected_regulator_serial != actual_regulator_serial
    )

    # Actual Cylinder ID
    cursor.execute("SELECT id FROM cylinders WHERE serial_number = ?", (actual_cylinder_serial,))
    cyl = cursor.fetchone()
    if not cyl:
        conn.close()
        raise ValueError(f"❌ Cylinder '{actual_cylinder_serial}' not found in system.")
    cylinder_id = cyl[0]

    # Actual Regulator ID
    cursor.execute("SELECT id FROM regulators WHERE serial_number = ?", (actual_regulator_serial,))
    reg = cursor.fetchone()
    if not reg:
        conn.close()
        raise ValueError(f"❌ Regulator '{actual_regulator_serial}' not found in system.")
    regulator_id = reg[0]

    # Var olan bir eşleşme var mı?
    cursor.execute("""
        SELECT id FROM scba_assemblies
        WHERE cylinder_id = ? AND regulator_id = ?
    """, (cylinder_id, regulator_id))
    match = cursor.fetchone()

    if match:
        assembly_id = match[0]
        result_msg = f"✅ Using existing SCBA assembly (ID: {assembly_id})"
    else:
        # Yeni eşleşme oluştur
        cursor.execute("""
            INSERT INTO scba_assemblies (cylinder_id, regulator_id, assigned_date, location, status)
            VALUES (?, ?, DATE('now'), '', 'Active')
        """, (cylinder_id, regulator_id))
        assembly_id = cursor.lastrowid
        result_msg = f"➕ New SCBA assembly created (ID: {assembly_id})"

    conn.commit()
    conn.close()
    return result_msg, assembly_id, updated


@app.route('/add-scba', methods=['GET', 'POST'])
@login_required
def add_scba():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        tag_number = request.form['tag_number'].strip().upper()
        brand = request.form['brand'].strip()
        model = request.form['model'].strip()
        cylinder_capacity = request.form['cylinder_capacity'].strip()
        cylinder_pressure = request.form['cylinder_pressure'].strip()
        refiling_date = request.form['refiling_date'].strip()
        hydro_test_date = request.form['hydro_test_date'].strip()
        cylinder_serial = request.form['cylinder_serial'].strip()
        regulator_serial = request.form['regulator_serial'].strip()
        remarks = request.form['remarks'].strip()
        location = request.form['location'].strip()

        # Mevcut tag_number var mı?
        existing = cursor.execute("SELECT * FROM scba_units WHERE tag_number = ?", (tag_number,)).fetchone()

        try:
            if existing:
                if not existing['brand'] and not existing['model'] and not existing['cylinder_serial']:
                    # Güncelleme yap
                    cursor.execute("""
                        UPDATE scba_units
                        SET brand=?, model=?, cylinder_capacity=?, cylinder_pressure=?,
                            refiling_date=?, hydro_test_date=?, cylinder_serial=?,
                            regulator_serial=?, remarks=?, location=?
                        WHERE tag_number=?
                    """, (
                        brand, model, cylinder_capacity, cylinder_pressure,
                        refiling_date, hydro_test_date, cylinder_serial,
                        regulator_serial, remarks, location, tag_number
                    ))
                    flash(f"✅ SCBA tag '{tag_number}' was pre-created and is now completed.", "success")
                else:
                    flash(f"❌ Tag '{tag_number}' already exists and is in use.", "danger")
                    conn.close()
                    return render_template('add_scba.html')
            else:
                # Yeni kayıt ekle
                cursor.execute("""
                    INSERT INTO scba_units (
                        tag_number, brand, model, cylinder_capacity, cylinder_pressure,
                        refiling_date, hydro_test_date, cylinder_serial,
                        regulator_serial, remarks, location
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tag_number, brand, model, cylinder_capacity, cylinder_pressure,
                    refiling_date, hydro_test_date, cylinder_serial,
                    regulator_serial, remarks, location
                ))
                flash(f"✅ New SCBA unit '{tag_number}' added successfully.", "success")

            # Cylinder ekle (eğer yoksa)
            cursor.execute("""
                INSERT OR IGNORE INTO cylinders (
                    serial_number, capacity, pressure, status, remarks
                ) VALUES (?, ?, ?, 'Active', ?)
            """, (cylinder_serial, cylinder_capacity, cylinder_pressure, f"From SCBA: {brand} {model}"))

            # Regulator ekle (eğer yoksa)
            cursor.execute("""
                INSERT OR IGNORE INTO regulators (
                    serial_number, brand, model, status, remarks
                ) VALUES (?, ?, ?, 'Active', ?)
            """, (regulator_serial, brand, model, f"From SCBA: {location}"))

            conn.commit()

        except sqlite3.IntegrityError:
            flash("❌ Integrity Error. Possible duplicate cylinder or regulator serial.", "danger")

    conn.close()
    return render_template('add_scba.html')


@app.route('/test-session')
def test_session():
    return str(dict(session))






#SCBA List


#from datetime import datetime, timedelta

@app.route('/scba-list')
@login_required
@role_required('admin', 'inspector')
def list_scba():
    from datetime import datetime, timedelta
    from flask import request

    conn = get_db_connection()
    cursor = conn.cursor()

    only_fails = request.args.get('only_fails') == '1'
    filter_type = request.args.get('filter')

    query = """
    SELECT s.*,
           i.inspection_date AS last_inspection,
           i.ldv_leak_test,
           i.whistle_test,
           i.mask_leak_test,
           i.overall_condition
    FROM scba_units s
    LEFT JOIN (
        SELECT *
        FROM scba_inspections
        WHERE id IN (
            SELECT MAX(id)
            FROM scba_inspections
            GROUP BY scba_id
        )
    ) i ON s.id = i.scba_id
    ORDER BY s.brand ASC
    """

    rows = cursor.execute(query).fetchall()
    scbas = []
    today = datetime.utcnow().date()

    for row in rows:
        scba = dict(row)

        # Gün farkı hesaplama
        if scba['last_inspection']:
            last_date = datetime.strptime(scba['last_inspection'], "%Y-%m-%d").date()
            scba['days_old'] = (today - last_date).days
        else:
            scba['days_old'] = None

        # Refiling alert
        if scba['refiling_date']:
            ref_date = datetime.strptime(scba['refiling_date'].split()[0], "%Y-%m-%d").date()
            scba['refiling_alert'] = (today - ref_date) > timedelta(days=180)
        else:
            scba['refiling_alert'] = False

        # Hydro test alert
        if scba['hydro_test_date']:
            test_date = datetime.strptime(scba['hydro_test_date'].split()[0], "%Y-%m-%d").date()
            expire_date = test_date + timedelta(days=5 * 365)
            scba['hydro_alert'] = today >= (expire_date - timedelta(days=90))
        else:
            scba['hydro_alert'] = False

        # Fail tespiti
        scba['has_fail'] = any([
            scba.get('ldv_leak_test') == 'Fail',
            scba.get('whistle_test') == 'Fail',
            scba.get('mask_leak_test') == 'Fail',
            scba.get('overall_condition') == 'Fail',
        ])

        scbas.append(scba)

    conn.close()

    # Filtreleme
    filtered_scbas = scbas
    if only_fails:
        filtered_scbas = [s for s in filtered_scbas if s['has_fail']]
    if filter_type == 'hydro_due':
        filtered_scbas = [s for s in filtered_scbas if s['hydro_alert']]

    return render_template(
        'scba_list.html',
        scbas=filtered_scbas,
        only_fails=only_fails,
        filter_type=filter_type
    )






###SCBA List


#SCBA INSPECTION REPORT

from flask import send_file, abort
from datetime import datetime
import sqlite3, os, io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

@app.route('/scba-report/<int:scba_id>')
@login_required
def scba_report(scba_id):
    def get_db_connection():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    def format_date_dd_mmm_yyyy(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%b-%Y').upper()
        except:
            return date_str

    conn = get_db_connection()
    cursor = conn.cursor()

    scba = cursor.execute("SELECT * FROM scba_units WHERE id = ?", (scba_id,)).fetchone()
    inspections = cursor.execute("""
        SELECT * FROM scba_inspections
        WHERE scba_id = ?
        ORDER BY inspection_date DESC
    """, (scba_id,)).fetchall()
    conn.close()

    if not scba:
        abort(404, description="SCBA not found")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo (optional)
    logo_path = os.path.join("static", "Logo.jpg")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, x=40, y=height - 80, width=120, height=40, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, height - 50, "SCBA Inspection Report")

    # SCBA Information Table
    y = height - 100
    info = [
        ['Tag Number', scba['tag_number']],
        ['Cylinder Serial', scba['cylinder_serial']],
        ['Regulator Serial', scba['regulator_serial']],
        ['Brand / Model', f"{scba['brand']} / {scba['model']}"],
        ['Capacity / Pressure', f"{scba['cylinder_capacity']} / {scba['cylinder_pressure']}"],
        ['Refiling Date', format_date_dd_mmm_yyyy(scba['refiling_date'])],
        ['Hydro Test Date', format_date_dd_mmm_yyyy(scba['hydro_test_date'])],
        ['Location', scba['location']],
        ['Remarks', scba['remarks']]
    ]

    table = Table(info, colWidths=[120, 380])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    table.wrapOn(c, width - 100, height)
    table.drawOn(c, x=40, y=y - len(info)*18)

    # Inspection History Table
    y = y - len(info)*18 - 40
    if inspections:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Inspection History")
        y -= 20

        data = [['Date', 'Inspected By', 'Pressure', 'LDV', 'Mask', 'Whistle', 'Condition', 'Remarks']]
        for i in inspections:
            data.append([
                format_date_dd_mmm_yyyy(i['inspection_date']),
                i['inspected_by'],
                i['pressure_check'],
                i['ldv_leak_test'],
                i['mask_leak_test'],
                i['whistle_test'],
                i['overall_condition'],
                i['remarks'][:30]
            ])

        history_table = Table(data, colWidths=[60, 80, 50, 40, 40, 50, 60, 100])
        history_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        history_table.wrapOn(c, width - 80, height)
        history_table.drawOn(c, 40, y - len(data)*16)
        y -= len(data)*16 + 40

    # Signature Fields
    if y < 150:
        c.showPage()
        y = height - 100

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Inspector Signature:")
    c.line(160, y, 300, y)
    y -= 30
    c.drawString(50, y, "Date:")
    c.line(90, y, 160, y)

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"SCBA_Report_{scba['tag_number']}.pdf",
        mimetype='application/pdf'
    )



#### Fire extinguisher delete route
@app.route('/delete-extinguisher/<int:extinguisher_id>', methods=['GET'])
def delete_fire_extinguisher(extinguisher_id):
    if 'username' not in session:
        flash("Login required to delete extinguisher.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Silmeden önce extinguisher var mı kontrol et
    cursor.execute("SELECT * FROM fire_extinguishers WHERE id = ?", (extinguisher_id,))
    extinguisher = cursor.fetchone()

    if extinguisher:
        tag_number = extinguisher['tag_number']

        # İlgili inspection kayıtlarını da sil
        cursor.execute("DELETE FROM fire_extinguisher_inspections WHERE extinguisher_id = ?", (extinguisher_id,))
        cursor.execute("DELETE FROM fire_extinguishers WHERE id = ?", (extinguisher_id,))
        conn.commit()

        flash(f"🗑️ Extinguisher '{tag_number}' deleted successfully.", "success")
    else:
        flash("Extinguisher not found.", "warning")

    conn.close()
    return redirect(url_for('list_fire_extinguishers'))








#SCBA INSPECTION REPORT END

@app.route('/inspect-scba-tag/<tag>', methods=['GET', 'POST'])
def inspect_scba_by_tag(tag):
    from datetime import date
    from flask import abort
    conn = get_db_connection()
    cursor = conn.cursor()

    tag_upper = tag.strip().upper()

    scba = cursor.execute("""
        SELECT id, tag_number, brand, model, cylinder_serial, regulator_serial,
               cylinder_capacity, cylinder_pressure,
               refiling_date, hydro_test_date, location, remarks
        FROM scba_units
        WHERE UPPER(tag_number) = ?
    """, (tag_upper,)).fetchone()

    conn.close()

    if not scba:
        flash(f"⚠️ SCBA unit not found with given TAG: {tag}", "danger")
        return redirect(url_for('list_scba'))

    # Gerekli alanlar boşsa yönlendir
    if not all([scba['brand'], scba['model'], scba['cylinder_serial'], scba['regulator_serial']]):
        flash(f"ℹ️ SCBA tag '{tag_upper}' is incomplete. Please complete the SCBA record.", "warning")
        return redirect(url_for('add_scba', tag_number=tag_upper))

    return redirect(url_for('inspect_scba', scba_id=scba['id']))











@app.route('/inspect-scba-new', methods=['GET', 'POST'])
def inspect_assembly():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tüm silindir ve regülatörleri al
    cylinders = cursor.execute("SELECT id, serial_number FROM cylinders ORDER BY serial_number ASC").fetchall()
    regulators = cursor.execute("SELECT id, serial_number FROM regulators ORDER BY serial_number ASC").fetchall()

    if request.method == 'POST':
        cylinder_id = request.form['cylinder_id']
        regulator_id = request.form['regulator_id']
        inspected_by = request.form['inspected_by']
        inspection_date = request.form['inspection_date']
        pressure_check = request.form['pressure_check']
        ldv = request.form['ldv_leak_test']
        mask = request.form['mask_leak_test']
        whistle = request.form['whistle_test']
        condition = request.form['overall_condition']
        remarks = request.form['remarks']

        # 1️⃣ Mevcut eşleşme var mı?
        result = cursor.execute("""
            SELECT id FROM scba_assemblies
            WHERE cylinder_id = ? AND regulator_id = ?
        """, (cylinder_id, regulator_id)).fetchone()

        if result:
            scba_id = result['id']
        else:
            # 2️⃣ Yoksa yeni eşleşme oluştur
            cursor.execute("""
                INSERT INTO scba_assemblies (cylinder_id, regulator_id, assigned_date, location, status)
                VALUES (?, ?, DATE('now'), '', 'Active')
            """, (cylinder_id, regulator_id))
            scba_id = cursor.lastrowid

        # 3️⃣ Inspection kaydını oluştur
        cursor.execute("""
            INSERT INTO scba_inspections (
                scba_id, inspection_date, inspected_by,
                pressure_check, ldv_leak_test, mask_leak_test,
                whistle_test, overall_condition, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scba_id, inspection_date, inspected_by,
            pressure_check, ldv, mask, whistle, condition, remarks
        ))

        conn.commit()
        conn.close()
        flash("✅ Inspection recorded successfully", "success")
        return redirect(url_for('list_scba'))

    conn.close()
    return render_template('inspect_assembly_form.html',
                           cylinders=cylinders,
                           regulators=regulators)


@app.route('/assemblies')
def list_assemblies():
    from datetime import datetime
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        a.id AS assembly_id,
        a.assigned_date,
        a.location,
        c.serial_number AS cylinder_serial,
        c.capacity,
        c.pressure,
        r.serial_number AS regulator_serial,
        r.brand,
        r.model,
        i.inspection_date,
        i.ldv_leak_test,
        i.whistle_test,
        i.mask_leak_test,
        i.overall_condition
    FROM scba_assemblies a
    JOIN cylinders c ON a.cylinder_id = c.id
    JOIN regulators r ON a.regulator_id = r.id
    LEFT JOIN (
        SELECT *
        FROM scba_inspections
        WHERE (scba_id, inspection_date) IN (
            SELECT scba_id, MAX(inspection_date)
            FROM scba_inspections
            GROUP BY scba_id
        )
    ) i ON i.scba_id = a.id
    ORDER BY a.assigned_date DESC
    """

    rows = cursor.execute(query).fetchall()
    assemblies = []

    for row in rows:
        asm = dict(row)
        asm['has_fail'] = any([
            asm.get('ldv_leak_test') == 'Fail',
            asm.get('whistle_test') == 'Fail',
            asm.get('mask_leak_test') == 'Fail',
            asm.get('overall_condition') == 'Fail',
        ])
        assemblies.append(asm)

    conn.close()
    return render_template('scba_assembly_list.html', assemblies=assemblies)


@app.route('/export-scba-excel')
def export_scba_excel():
    import pandas as pd
    from flask import send_file
    import io
    import sqlite3

    try:
        # 📥 Veritabanından veri çek
        conn = sqlite3.connect(DATABASE)
        df = pd.read_sql_query("SELECT * FROM scba_units ORDER BY brand ASC", conn)
        conn.close()

        # 🧪 Excel'e yaz
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='SCBA List')

        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name='SCBA_Export.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error while exporting Excel: {str(e)}", 500


@app.route('/inspect-scba/<int:scba_id>', methods=['GET', 'POST'])
def inspect_scba(scba_id):
    from datetime import date
    conn = get_db_connection()
    cursor = conn.cursor()

    # SCBA birimini getir
    scba = cursor.execute("""
        SELECT id, tag_number, brand, model, cylinder_serial, regulator_serial,
               cylinder_capacity, cylinder_pressure,
               refiling_date, hydro_test_date, location, remarks
        FROM scba_units
        WHERE id = ?
    """, (scba_id,)).fetchone()

    if not scba:
        flash("SCBA unit not found.", "danger")
        return redirect(url_for('list_scba'))

    if request.method == 'POST':
        inspection_date = request.form['inspection_date']
        inspected_by = request.form['inspected_by']
        pressure_check = request.form['pressure_check']
        ldv = request.form['ldv_leak_test']
        mask = request.form['mask_leak_test']
        whistle = request.form['whistle_test']
        condition = request.form['overall_condition']
        remarks = request.form['remarks']
        inspection_remarks = request.form['inspection_remarks']
        refiling_date = request.form['refiling_date']
        hydro_test_date = request.form['hydro_test_date']
        location = request.form['location']
        actual_cylinder_serial = request.form['cylinder_serial'].strip()
        actual_regulator_serial = request.form['regulator_serial'].strip()

        # Seri numarası uyumu
        if (scba['cylinder_serial'] == actual_cylinder_serial and
            scba['regulator_serial'] == actual_regulator_serial):
            result = "✅ SCBA serial numbers match."
            updated = False
        else:
            result = "⚠️ Serial numbers do not match. Inspection recorded anyway."
            updated = True

        # Denetim kaydı
        cursor.execute("""
            INSERT INTO scba_inspections (
                scba_id, inspection_date, inspected_by,
                pressure_check, ldv_leak_test, mask_leak_test,
                whistle_test, overall_condition, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scba_id, inspection_date, inspected_by,
            pressure_check, ldv, mask, whistle, condition, inspection_remarks
        ))

        # SCBA verilerini güncelle
        cursor.execute("""
            UPDATE scba_units
            SET refiling_date = ?, hydro_test_date = ?, location = ?, remarks = ?
            WHERE id = ?
        """, (refiling_date, hydro_test_date, location, remarks, scba_id))

        conn.commit()
        conn.close()

        flash(result, "info" if updated else "success")
        return redirect(url_for('list_scba'))

    # Eski inspection kayıtları
    inspections = cursor.execute("""
        SELECT * FROM scba_inspections
        WHERE scba_id = ?
        ORDER BY inspection_date DESC
    """, (scba_id,)).fetchall()

    conn.close()

    # Şablona gönderilecek veri
    return render_template(
        'scba_inspection_form.html',
        scba=scba,
        inspections=inspections,
        current_date=date.today().isoformat(),
        qr_link=f"https://mytestapp.pythonanywhere.com/inspect-scba-tag/{scba['tag_number']}"
    )




@app.route('/export-scba-pdf')
def export_scba_pdf():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    import pandas as pd
    import sqlite3
    import io
    import os
    from datetime import datetime
    from flask import send_file

    # 🔧 Yardımcı tarih fonksiyonları
    def strip_time_part(date_str):
        try:
            return date_str.split(' ')[0]
        except:
            return date_str

    def format_date_dd_mmm_yyyy(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%b-%Y').upper()
        except:
            return date_str if date_str else "--"

    # 📥 Veritabanından veri çek
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("""
        SELECT tag_number, brand, model, cylinder_capacity, cylinder_pressure,
               refiling_date, hydro_test_date,
               cylinder_serial, regulator_serial, location, remarks
        FROM scba_units
        ORDER BY tag_number ASC
    """, conn)
    conn.close()

    # 🎯 Tarihleri düzenle
    df['refiling_date'] = df['refiling_date'].apply(strip_time_part).apply(format_date_dd_mmm_yyyy)
    df['hydro_test_date'] = df['hydro_test_date'].apply(strip_time_part).apply(format_date_dd_mmm_yyyy)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=100,
        bottomMargin=40
    )

    elements = []
    total_scba = len(df)

    # 🖼 Logo, başlık ve sayfa numarası
    def header_canvas(c, doc):
        logo_path = os.path.join('static', 'Logo.jpg')
        if os.path.exists(logo_path):
            c.drawImage(ImageReader(logo_path), 20, doc.pagesize[1] - 60, width=110, height=35)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(doc.pagesize[0] / 2, doc.pagesize[1] - 80, "SCBA Equipment List")
        c.setFont("Helvetica", 10)
        c.drawString(150, doc.pagesize[1] - 100, f"Total SCBA Units: {total_scba}")
        c.setFont("Helvetica", 9)
        c.drawRightString(doc.pagesize[0] - 30, 20, f"Page {doc.page}")

    # 🔠 Başlıklar
    header = [
        "TAG", "Brand", "Model", "Capacity", "Pressure",
        "Refiling Date", "Hydro Test Date",
        "Cylinder SN", "Regulator SN", "Location", "Remarks"
    ]

    records_per_page = 30
    data_rows = df[[
        "tag_number", "brand", "model", "cylinder_capacity", "cylinder_pressure",
        "refiling_date", "hydro_test_date", "cylinder_serial",
        "regulator_serial", "location", "remarks"
    ]].fillna('-').values.tolist()

    # 🧾 Sayfalara böl
    for i in range(0, len(data_rows), records_per_page):
        chunk = data_rows[i:i + records_per_page]
        table_data = [header] + chunk

        t = Table(table_data, colWidths=[
            50,   # TAG
            60,   # Brand
            100,  # Model
            50,   # Capacity
            50,   # Pressure
            70,   # Refiling Date
            70,   # Hydro Test Date
            80,   # Cylinder SN
            80,   # Regulator SN
            70,   # Location
            120   # Remarks
        ])

        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ]))
        elements.append(t)
        if i + records_per_page < len(data_rows):
            elements.append(PageBreak())

    doc.build(elements, onFirstPage=header_canvas, onLaterPages=header_canvas)

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name='SCBA_List_with_Logo.pdf',
        mimetype='application/pdf'
    )



#EDIT SCBA

@app.route('/edit-scba/<int:scba_id>', methods=['GET', 'POST'])
@login_required
def edit_scba(scba_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # SCBA verisini çek
    scba = cursor.execute("SELECT * FROM scba_units WHERE id = ?", (scba_id,)).fetchone()

    if not scba:
        conn.close()
        flash("SCBA unit not found.", "danger")
        return redirect(url_for('list_scba'))

    if request.method == 'POST':
        # Form verilerini al
        tag_number = request.form['tag_number']
        brand = request.form['brand']
        model = request.form['model']
        cylinder_capacity = request.form['cylinder_capacity']
        cylinder_pressure = request.form['cylinder_pressure']
        refiling_date = request.form['refiling_date']
        hydro_test_date = request.form['hydro_test_date']
        cylinder_serial = request.form['cylinder_serial']
        regulator_serial = request.form['regulator_serial']
        remarks = request.form['remarks']
        location = request.form['location']

        # Güncelle
        cursor.execute("""
            UPDATE scba_units SET
                tag_number = ?, brand = ?, model = ?, cylinder_capacity = ?, cylinder_pressure = ?,
                refiling_date = ?, hydro_test_date = ?, cylinder_serial = ?, regulator_serial = ?,
                remarks = ?, location = ?
            WHERE id = ?
        """, (
            tag_number, brand, model, cylinder_capacity, cylinder_pressure,
            refiling_date, hydro_test_date, cylinder_serial, regulator_serial,
            remarks, location, scba_id
        ))
        conn.commit()
        conn.close()
        flash("✅ SCBA unit updated successfully.", "success")
        return redirect(url_for('list_scba'))

    conn.close()
    return render_template('edit_scba.html', scba=scba)



#EDIT SCBA


@app.route('/delete-scba/<int:scba_id>', methods=['POST'])
def delete_scba(scba_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scba_units WHERE id = ?", (scba_id,))
    conn.commit()
    conn.close()
    flash("SCBA unit deleted.", "success")
    return redirect(url_for('list_scba'))


# SCBA BULK UPLOAD

@app.route('/upload-scba', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def upload_scba():
    conn = get_db_connection()
    cursor = conn.cursor()
    skipped = []
    print("📄 Aktif DB Dosyası:", os.path.abspath(DATABASE))

    def get_next_tag_number():
        last = cursor.execute("""
            SELECT tag_number FROM scba_units
            WHERE tag_number LIKE 'SCBA-%'
            ORDER BY CAST(SUBSTR(tag_number, 6) AS INTEGER) DESC LIMIT 1
        """).fetchone()
        if last and last['tag_number'][5:].isdigit():
            next_number = int(last['tag_number'][5:]) + 1
        else:
            next_number = 1
        return f"SCBA-{str(next_number).zfill(4)}"

    if request.method == 'POST':
        file = request.files.get('excel_file')
        if file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)

            required_cols = [
                'tag_number', 'brand', 'model', 'cylinder_capacity', 'cylinder_pressure',
                'refiling_date', 'hydro_test_date', 'cylinder_serial',
                'regulator_serial', 'remarks', 'location'
            ]
            if all(col in df.columns for col in required_cols):
                added = 0
                for _, row in df.iterrows():
                    row_data = {}
                    for col in required_cols:
                        row_data[col] = str(row[col]).strip() if pd.notna(row[col]) else ""

                    # Otomatik TAG üretimi
                    if not row_data['tag_number']:
                        row_data['tag_number'] = get_next_tag_number()

                    try:
                        cursor.execute("""
                            INSERT INTO scba_units (
                                tag_number, brand, model, cylinder_capacity, cylinder_pressure,
                                refiling_date, hydro_test_date, cylinder_serial,
                                regulator_serial, remarks, location
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row_data['tag_number'], row_data['brand'], row_data['model'],
                            row_data['cylinder_capacity'], row_data['cylinder_pressure'],
                            row_data['refiling_date'], row_data['hydro_test_date'],
                            row_data['cylinder_serial'], row_data['regulator_serial'],
                            row_data['remarks'], row_data['location']
                        ))
                        added += 1
                    except sqlite3.IntegrityError:
                        skipped.append(row_data['tag_number'])

                conn.commit()
                flash(f"✅ {added} SCBA unit(s) added.", "success")
                if skipped:
                    flash(f"⚠️ {len(skipped)} duplicate TAG(s) skipped:<br>" + "<br>".join(skipped), "danger")
            else:
                flash("❌ Excel must contain correct headers.", "danger")
        else:
            flash("❌ Invalid file type. Please upload a .xlsx file.", "warning")

    conn.close()
    return render_template('upload_scba.html')



# SCBA BULK UPLOAD son



### Ana Sayfa Icerigi basla
from flask import render_template, session
from datetime import datetime, timedelta
from auth_utils import login_required


@app.route('/')
@login_required
def home():
    full_name = session.get('full_name', 'User')
    role = session.get('role', 'viewer')

    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.today().date()
    soon = today + timedelta(days=7)

    # 🔹 Fire Extinguisher Monthly Due Breakdown
    cursor.execute("""SELECT COUNT(*) FROM fire_extinguishers WHERE monthly_due_date IS NOT NULL AND date(monthly_due_date) > date(?)""", (soon,))
    monthly_ok = cursor.fetchone()[0] or 0

    cursor.execute("""SELECT COUNT(*) FROM fire_extinguishers WHERE monthly_due_date IS NOT NULL AND date(monthly_due_date) BETWEEN date(?) AND date(?)""", (today, soon))
    monthly_soon = cursor.fetchone()[0] or 0

    cursor.execute("""SELECT COUNT(*) FROM fire_extinguishers WHERE monthly_due_date IS NOT NULL AND date(monthly_due_date) < date(?)""", (today,))
    monthly_overdue = cursor.fetchone()[0] or 0

    monthly_due_counts = [monthly_ok, monthly_soon, monthly_overdue]

    # 🔹 Fire Extinguisher 3rd Party Due Breakdown
    cursor.execute("""SELECT COUNT(*) FROM fire_extinguishers WHERE third_party_due_date IS NOT NULL AND date(third_party_due_date) > date(?)""", (soon,))
    tp_ok = cursor.fetchone()[0] or 0

    cursor.execute("""SELECT COUNT(*) FROM fire_extinguishers WHERE third_party_due_date IS NOT NULL AND date(third_party_due_date) BETWEEN date(?) AND date(?)""", (today, soon))
    tp_soon = cursor.fetchone()[0] or 0

    cursor.execute("""SELECT COUNT(*) FROM fire_extinguishers WHERE third_party_due_date IS NOT NULL AND date(third_party_due_date) < date(?)""", (today,))
    tp_overdue = cursor.fetchone()[0] or 0

    third_party_due_counts = [tp_ok, tp_soon, tp_overdue]

    # 🔹 Toplam Sayılar
    cursor.execute("SELECT COUNT(*) FROM scba_units")
    total_scba = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM fire_extinguishers")
    total_extinguishers = cursor.fetchone()[0] or 0

    try:
        cursor.execute("SELECT COUNT(*) FROM area_gas_monitors")
        total_monitors = cursor.fetchone()[0] or 0

        monitor_status_counts = []
        for status in ['Active', 'Inactive', 'Service']:
            cursor.execute("SELECT COUNT(*) FROM area_gas_monitors WHERE status = ?", (status,))
            monitor_status_counts.append(cursor.fetchone()[0] or 0)

        cursor.execute("""SELECT gas_type, COUNT(*) FROM area_gas_monitors
                          WHERE gas_type IS NOT NULL AND gas_type != ''
                          GROUP BY gas_type""")
        gas_rows = cursor.fetchall()
        gas_types = [row[0] for row in gas_rows]
        gas_type_counts = [row[1] for row in gas_rows]
    except Exception as e:
        print("⚠️ area_gas_monitors hatası:", e)
        total_monitors = 0
        monitor_status_counts = [0, 0, 0]
        gas_types = []
        gas_type_counts = []

    # 🔹 Fire Extinguisher Condition Breakdown
    extinguisher_condition_counts = []
    for condition in ["Good", "Needs Maintenance"]:
        cursor.execute("SELECT COUNT(*) FROM fire_extinguishers WHERE LOWER(TRIM(overall_condition)) = ?", (condition.lower(),))
        extinguisher_condition_counts.append(cursor.fetchone()[0] or 0)

    # 🔹 SCBA Refiling History
    cursor.execute("""
        SELECT strftime('%Y-%m', refiling_date) as month, COUNT(*)
        FROM scba_units
        WHERE refiling_date IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """)
    scba_rows = cursor.fetchall()
    scba_months = [row[0] for row in reversed(scba_rows)]
    scba_counts = [row[1] for row in reversed(scba_rows)]

    conn.close()

    return render_template(
        'index.html',
        full_name=full_name,
        role=role,
        total_scba=total_scba,
        total_extinguishers=total_extinguishers,
        total_monitors=total_monitors,
        extinguisher_condition_counts=extinguisher_condition_counts,
        third_party_due_counts=third_party_due_counts,
        monthly_due_counts=monthly_due_counts,
        scba_months=scba_months,
        scba_counts=scba_counts,
        monitor_status_counts=monitor_status_counts,
        gas_types=gas_types,
        gas_type_counts=gas_type_counts
    )


## Ana Sayfa Icerigi Son

### API
from flask import jsonify

@app.route('/api/extinguisher-conditions')
@login_required  # Giriş yapılmamışsa login sayfasına yönlendirir
def api_extinguisher_conditions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Tüm good / needs maintenance verilerini çek
        cursor.execute("""
            SELECT LOWER(TRIM(overall_condition)) as cond, COUNT(*)
            FROM fire_extinguishers
            WHERE overall_condition IS NOT NULL AND TRIM(overall_condition) != ''
            GROUP BY cond
        """)
        rows = cursor.fetchall()
        conn.close()

        # Etiketleri normalize et
        label_map = {
            'good': 'Good',
            'needs maintenance': 'Needs Maintenance'
        }

        # Sıralama garantisi için:
        final_labels = ['Good', 'Needs Maintenance']
        final_counts = [0, 0]  # default

        for row in rows:
            raw_label = row[0]
            count = row[1]
            if raw_label in label_map:
                std_label = label_map[raw_label]
                idx = final_labels.index(std_label)
                final_counts[idx] = count

        return jsonify({
            "labels": final_labels,
            "counts": final_counts
        })

    except Exception as e:
        # Konsola da yaz, hatayı döndür
        print("API Error:", e)
        return jsonify({"error": "Internal error", "details": str(e)}), 500


###API Area Gas monitor
@app.route('/api/monitor-status')
def api_monitor_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    labels = ['Active', 'Inactive', 'Service']
    counts = []
    for label in labels:
        cursor.execute("SELECT COUNT(*) FROM area_gas_monitors WHERE status = ?", (label,))
        counts.append(cursor.fetchone()[0])
    conn.close()
    return jsonify({"labels": labels, "counts": counts})



### API SON



import pandas as pd  # en üste eklenmiş olmalı

@app.route('/add-user', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector') # sadece bu roller erişebilir
def add_user():
    conn = get_db_connection()
    cursor = conn.cursor()

    skipped_conflict = []  # Badge + farklı isim çakışmalarını burada tutacağız
    added = 0

    if request.method == 'POST':
        # ✅ BULK UPLOAD (Excel dosyasından)
        if 'bulk_submit' in request.form:
            file = request.files.get('bulk_file')
            if file and file.filename.endswith('.xlsx'):
                try:
                    df = pd.read_excel(file)
                except Exception as e:
                    flash(f"Error reading Excel file: {e}", "danger")
                    df = None

                if df is not None and 'badge_number' in df.columns and 'full_name' in df.columns:
                    for _, row in df.iterrows():
                        badge = str(row['badge_number']).strip()
                        name = str(row['full_name']).strip()

                        if not badge or not name:
                            continue

                        # Var mı?
                        cursor.execute("SELECT full_name FROM users WHERE badge_number = ?", (badge,))
                        existing = cursor.fetchone()

                        if existing:
                            if existing['full_name'].strip().lower() != name.lower():
                                skipped_conflict.append(
                                    f"{badge} → Excel: {name} / System: {existing['full_name']}"
                                )
                        else:
                            cursor.execute("INSERT INTO users (badge_number, full_name) VALUES (?, ?)", (badge, name))
                            added += 1

                    conn.commit()

                    if added:
                        flash(f"{added} new user(s) added from Excel.", "success")
                    if skipped_conflict:
                        flash(f"⚠️ {len(skipped_conflict)} conflict(s) detected and skipped.", "danger")
                else:
                    flash("Excel file must contain 'badge_number' and 'full_name' columns.", "danger")
            else:
                flash("Please upload a valid .xlsx file.", "warning")

        # ✅ TEK KULLANICI EKLEME (formdan)
        else:
            badge_number = request.form['badge_number'].strip()
            full_name = request.form['full_name'].strip()

            if not badge_number or not full_name:
                flash("Both badge number and full name are required.", "danger")
            else:
                cursor.execute("SELECT full_name FROM users WHERE badge_number = ?", (badge_number,))
                existing = cursor.fetchone()

                if existing:
                    if existing['full_name'].strip().lower() == full_name.lower():
                        flash("This badge number is already registered with the same name.", "info")
                    else:
                        flash(f"❗ This badge number already belongs to '{existing['full_name']}'. Please check the name.", "danger")
                else:
                    cursor.execute("INSERT INTO users (badge_number, full_name) VALUES (?, ?)", (badge_number, full_name))
                    conn.commit()
                    flash("User added successfully.", "success")

    # 🟡 Tüm kullanıcıları ve varsa çakışmaları şablona gönder
    users = cursor.execute("SELECT badge_number, full_name FROM users ORDER BY full_name ASC").fetchall()
    conn.close()
    return render_template('add_user.html', users=users, conflicts=skipped_conflict)









@app.route('/products')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def list_products():
    brand_filter = request.args.get('brand')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    inspection_date_filter = request.args.get('inspection_date')

    query = """
    SELECT products.*, brands.name as brand_name
    FROM products
    LEFT JOIN brands ON products.brand_id = brands.id
    WHERE 1=1
    """
    params = []

    if brand_filter:
        query += " AND products.brand_id = ?"
        params.append(brand_filter)

    if type_filter:
        query += " AND products.type = ?"
        params.append(type_filter)

    if status_filter:
        query += " AND products.status = ?"
        params.append(status_filter)

    if inspection_date_filter:
        query += " AND products.inspection_date <= ?"
        params.append(inspection_date_filter)

    products = query_db(query, params)

    # Brand dropdown için
    brands = query_db("SELECT id, name FROM brands ORDER BY name ASC")
    types = [row['type'] for row in query_db("SELECT DISTINCT type FROM products")]

    # Kartlar için toplamları brand_id üzerinden alıyoruz
    brand_totals = query_db("""
    SELECT brands.name as brand_name, COUNT(products.id) as total_items
    FROM products
    LEFT JOIN brands ON products.brand_id = brands.id
    GROUP BY brands.name
""")


    return render_template('products.html',
                           products=products,
                           brand_totals=brand_totals,
                           brands=brands,
                           types=types)







@app.route('/inspect/<int:product_id>', methods=['GET', 'POST'])
def inspect_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if request.method == 'POST':
        inspection_date = request.form.get('inspection_date')
        inspected_by = request.form.get('inspected_by')
        inspection_result = request.form.get('inspection_result')
        notes = request.form.get('notes')

        # Inspection verisini inspections tablosuna kaydet
        conn.execute('''
            INSERT INTO inspections (
                product_id, inspection_date, inspected_by, inspection_result, notes
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            product_id,
            inspection_date,
            inspected_by,
            inspection_result,
            notes
        ))

        # Inspection sonucuna göre Product status bilgisini güncelle
        if inspection_result == 'Pass':
            new_status = 'OK'
        elif inspection_result == 'Needs Repair':
            new_status = 'Needs Repair'
        else:  # Fail
            new_status = 'Out of Service'

        conn.execute('UPDATE products SET status = ? WHERE id = ?', (new_status, product_id))

        conn.commit()
        conn.close()
        return redirect(url_for('list_products'))

    conn.close()
    return render_template('inspect_general.html', product=product)

@app.route('/inspection-log/<int:product_id>')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def inspection_log(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    logs = conn.execute('''
        SELECT * FROM inspections
        WHERE product_id = ?
        ORDER BY inspection_date DESC
    ''', (product_id,)).fetchall()
    conn.close()
    return render_template('inspection_log.html', product=product, logs=logs)

@app.route('/assign-product', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # sadece bu roller erişebilir
def assign_product():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        assigned_to = request.form['assigned_to'].strip()
        badge_number = request.form['badge_number'].strip()
        product_ids = request.form.getlist('product_ids')
        assigned_date = request.form['assigned_date']
        notes = request.form.get('notes', '')

        # Badge boşsa uyar
        if not badge_number:
            flash("Badge Number is required.", "danger")
            products = cursor.execute(
                "SELECT id, name, serial_id FROM products WHERE id NOT IN (SELECT product_id FROM assignments WHERE return_date IS NULL)"
            ).fetchall()
            conn.close()
            return render_template('assign_product.html', products=products)

        # Badge sistemde var mı, varsa isim aynı mı?
        cursor.execute("SELECT full_name FROM users WHERE badge_number = ?", (badge_number,))
        existing = cursor.fetchone()

        if existing:
            if existing['full_name'].strip().lower() != assigned_to.lower():
                flash(f"This badge number is already registered to '{existing['full_name']}'. Please correct the name.", "danger")
                products = cursor.execute(
                    "SELECT id, name, serial_id FROM products WHERE id NOT IN (SELECT product_id FROM assignments WHERE return_date IS NULL)"
                ).fetchall()
                conn.close()
                return render_template('assign_product.html', products=products)
        else:
            # İlk kez girilen badge → kullanıcı tablosuna kaydet
            cursor.execute("INSERT INTO users (badge_number, full_name) VALUES (?, ?)", (badge_number, assigned_to))

        # Ürünleri ata
        for product_id in product_ids:
            cursor.execute(
                "INSERT INTO assignments (product_id, assigned_to, badge_number, assigned_date, notes) VALUES (?, ?, ?, ?, ?)",
                (product_id, assigned_to, badge_number, assigned_date, notes)
            )

        conn.commit()

    # Sayfa GET ile açıldığında ürün listesi göster
    products = cursor.execute(
        "SELECT id, name, serial_id FROM products WHERE id NOT IN (SELECT product_id FROM assignments WHERE return_date IS NULL)"
    ).fetchall()

    conn.close()
    return render_template('assign_product.html', products=products)







@app.route('/assignments')
@login_required
@role_required('admin', 'inspector', 'viewer') # sadece bu roller erişebilir
def list_assignments():
    conn = get_db()
    cursor = conn.cursor()

    assignments = cursor.execute('''
        SELECT
            assignments.id,
            products.name as product_name,
            products.serial_id,
            assignments.assigned_to,
            assignments.badge_number,
            assignments.assigned_date,
            assignments.return_date,
            assignments.notes
        FROM assignments
        JOIN products ON assignments.product_id = products.id
        ORDER BY assignments.assigned_to, assignments.assigned_date DESC
    ''').fetchall()

    conn.close()

    # Kişiye göre grupla
    grouped_assignments = defaultdict(list)
    for assignment in assignments:
        grouped_assignments[assignment['assigned_to']].append(assignment)

    return render_template('assignments.html', grouped_assignments=grouped_assignments)




@app.route('/generate-pdf/<assigned_to>')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def generate_pdf(assigned_to):
    conn = get_db()
    cursor = conn.cursor()

    # Tüm atamaları çek
    assignments = cursor.execute('''
        SELECT
            products.name as product_name,
            products.serial_id,
            assignments.assigned_date,
            assignments.return_date,
            assignments.notes
        FROM assignments
        JOIN products ON assignments.product_id = products.id
        WHERE assignments.assigned_to = ?
    ''', (assigned_to,)).fetchall()

    # Badge Number'ı ayrıca çek (boş değilse en güncel olanı al)
    badge_row = cursor.execute('''
        SELECT badge_number FROM assignments
        WHERE assigned_to = ? AND badge_number IS NOT NULL
        ORDER BY assigned_date DESC LIMIT 1
    ''', (assigned_to,)).fetchone()
    conn.close()

    badge = badge_row['badge_number'] if badge_row and badge_row['badge_number'] else "Not Provided"

    if not assignments:
        return "No assignments found", 404

    # PDF oluştur
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo ortada ve büyük
    logo_path = os.path.join('static', 'logo.jpg')
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        logo_width = 200
        logo_height = 80
        x = (width - logo_width) / 2
        y = height - 100
        p.drawImage(logo, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')

    # Başlık
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 130, f"Assignment Report - {assigned_to} (Badge: {badge})")

    # Tablo başlıkları
    p.setFont("Helvetica-Bold", 12)
    y = height - 170
    p.drawString(50, y, "Product Name")
    p.drawString(250, y, "Serial No")
    p.drawString(400, y, "Assigned Date")
    y -= 20

    p.setFont("Helvetica", 11)

    for assignment in assignments:
        p.drawString(50, y, assignment['product_name'])
        p.drawString(250, y, assignment['serial_id'])
        p.drawString(400, y, assignment['assigned_date'])
        y -= 20
        if y < 100:
            p.showPage()
            y = height - 50

    # İmza alanları
    if y < 200:
        p.showPage()
        y = height - 100

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y - 20, "Receiver's Signature:")
    p.line(50, y - 30, 250, y - 30)

    p.drawString(300, y - 20, "Issuer's Signature:")
    p.line(300, y - 30, 500, y - 30)

    y -= 70
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Date: ________________________________")

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"{assigned_to}_assignment_report.pdf", mimetype='application/pdf')


    print("assignments[0]['badge_number'] =", assignments[0]['badge_number'])

    if not assignments:
        return "No assignments found", 404

    # Create PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo - merkezde ve büyük
    logo_path = os.path.join('static', 'logo.jpg')
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        logo_width = 200
        logo_height = 80
        x = (width - logo_width) / 2
        y = height - 100
        p.drawImage(logo, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')

    # Başlık
    badge = assignments[0]['badge_number'] if assignments[0]['badge_number'] else "N/A"
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 130, f"Assignment Report - {assigned_to} (Badge: {badge})")

    # Table Header
    p.setFont("Helvetica-Bold", 12)
    y = height - 170
    p.drawString(50, y, "Product Name")
    p.drawString(250, y, "Serial No")
    p.drawString(400, y, "Assigned Date")
    y -= 20

    p.setFont("Helvetica", 11)

    for assignment in assignments:
        p.drawString(50, y, assignment['product_name'])
        p.drawString(250, y, assignment['serial_id'])
        p.drawString(400, y, assignment['assigned_date'])
        y -= 20
        if y < 100:
            p.showPage()
            y = height - 50

    # İmza alanları
    if y < 200:
        p.showPage()
        y = height - 100

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y - 20, "Receiver's Signature:")
    p.line(50, y - 30, 250, y - 30)

    p.drawString(300, y - 20, "Issuer's Signature:")
    p.line(300, y - 30, 500, y - 30)

    y -= 70
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Date: ________________________________")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{assigned_to}_assignment_report.pdf", mimetype='application/pdf')


@app.route('/return-product/<int:assignment_id>', methods=['POST'])
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def return_product(assignment_id):
    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('UPDATE assignments SET return_date = ? WHERE id = ?', (now, assignment_id))
    conn.commit()
    conn.close()

    return redirect('/assignments')






@app.route('/add-brand', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector') # sadece bu roller erişebilir
def add_brand():
    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        conn.execute('INSERT INTO brands (name) VALUES (?)', (name,))
        conn.commit()

    brands = conn.execute('SELECT * FROM brands').fetchall()
    conn.close()
    return render_template('add_brand.html', brands=brands)


from datetime import datetime, timedelta

@app.route('/add-product', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector') # sadece bu roller erişebilir
def add_product():
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    product_types = conn.execute('SELECT * FROM product_types').fetchall()

    if request.method == 'POST':
        brand_id = request.form['brand_id']
        serial_id = request.form['serial_id']
        name = request.form['product_name']
        quantity = request.form['product_quantity']
        type_ = request.form['product_type']
        details = request.form.get('product_details')
        first_inspection_date = request.form.get('first_inspection_date')
        inspection_period = request.form.get('inspection_period')  # yeni alan
        status = request.form.get('service_status')
        remarks = request.form.get('remarks')

        # next inspection date otomatik hesapla
        next_inspection_date = None
        if first_inspection_date and inspection_period:
            try:
                first_date_obj = datetime.strptime(first_inspection_date, '%Y-%m-%d')
                delta = timedelta(days=int(inspection_period))
                next_inspection_date = (first_date_obj + delta).strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Tarih hesaplama hatası: {e}")

        conn.execute('''INSERT INTO products
                        (brand_id, serial_id, name, quantity, type, details, first_inspection_date, inspection_date, status, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (brand_id, serial_id, name, quantity, type_, details, first_inspection_date, next_inspection_date, status, remarks))
        conn.commit()
        conn.close()
        return redirect(url_for('list_products'))

    conn.close()
    return render_template('add_product.html', brands=brands, product_types=product_types)



#SCBA manual scan
@app.route('/manual-scan-scba')
def manual_scan_scba():
    return render_template('manual_scan_scba.html')


#

@app.route('/add-bulk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def add_bulk():
    file_exists = os.path.exists('static/example_bulk_upload.xlsx')

    if request.method == 'POST':
        file = request.files['file']
        if file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)

                # 🔧 Tarihleri güvenli şekilde çevir
                df['first_inspection_date'] = pd.to_datetime(df['first_inspection_date'], errors='coerce')
                df['inspection_date'] = pd.to_datetime(df['inspection_date'], errors='coerce')

                # 🔒 Güvenli bağlantı
                with sqlite3.connect(DB_FILE, timeout=10) as conn:
                    cursor = conn.cursor()
                    for _, row in df.iterrows():
                        cursor.execute('''
                            INSERT INTO products (
                                brand_id, serial_id, name, quantity, type, details,
                                first_inspection_date, inspection_date, status, remarks
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row['brand_id'], row['serial_id'], row['name'], row['quantity'],
                            row.get('type'), row.get('details'),
                            row['first_inspection_date'].strftime('%Y-%m-%d') if pd.notnull(row['first_inspection_date']) else None,
                            row['inspection_date'].strftime('%Y-%m-%d') if pd.notnull(row['inspection_date']) else None,
                            row.get('status'), row.get('remarks')
                        ))

                return redirect(url_for('list_products'))

            except Exception as e:
                flash(f"Error during bulk upload: {str(e)}", "danger")
                return redirect(url_for('add_bulk'))

        else:
            flash("Invalid file type. Please upload an .xlsx file.", "warning")
            return redirect(url_for('add_bulk'))

    return render_template('add_bulk.html', file_exists=file_exists)


@app.route('/add-company', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector') # sadece bu roller erişebilir
def add_company():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        company_name = request.form['company_name'].strip()
        if company_name:
            try:
                cursor.execute("INSERT INTO companies (company_name) VALUES (?)", (company_name,))
                conn.commit()
                flash("Company added successfully.", "success")
            except sqlite3.IntegrityError:
                flash("This company already exists.", "warning")
    companies = cursor.execute("SELECT * FROM companies ORDER BY company_name ASC").fetchall()
    conn.close()
    return render_template('add_company.html', companies=companies)


@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_products'))



@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    product_types = conn.execute('SELECT * FROM product_types').fetchall()

    if request.method == 'POST':
        brand_id = request.form['brand_id']
        serial_id = request.form['serial_id']
        name = request.form['product_name']
        type_ = request.form['product_type']
        quantity = request.form['product_quantity']
        details = request.form['product_details']
        first_inspection_date = request.form['first_inspection_date']
        next_inspection_date = request.form['next_inspection_date']
        status = request.form['service_status']
        remarks = request.form['remarks']

        conn.execute('''UPDATE products SET
                            brand_id = ?, serial_id = ?, name = ?, type = ?, quantity = ?, details = ?,
                            first_inspection_date = ?, inspection_date = ?, status = ?, remarks = ?
                        WHERE id = ?''',
                     (brand_id, serial_id, name, type_, quantity, details,
                      first_inspection_date, next_inspection_date, status, remarks, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('list_products'))

    conn.close()
    return render_template('edit_product.html', product=product, brands=brands, product_types=product_types)


@app.route('/add-product-type', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector') # sadece bu roller erişebilir
def add_product_type():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS product_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)')

    if request.method == 'POST':
        type_name = request.form['type_name']
        try:
            conn.execute('INSERT INTO product_types (name) VALUES (?)', (type_name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # aynı isimde varsa ekleme

    # 🔽 BU SATIR ÖNEMLİ — kayıtları şablona gönderiyoruz
    product_types = conn.execute('SELECT * FROM product_types').fetchall()
    conn.close()
    return render_template('add_product_type.html', product_types=product_types)


@app.route('/delete-product-type/<int:type_id>', methods=['POST'])
def delete_product_type(type_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM product_types WHERE id = ?', (type_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('add_product_type'))

from datetime import datetime, timedelta

from flask import render_template
from datetime import datetime, timedelta
import sqlite3

@app.route('/dashboard')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)

    overdue = cursor.execute("""
        SELECT COUNT(*) FROM fire_extinguishers
        WHERE third_party_due_date < ? OR monthly_due_date < ?
    """, (today, today)).fetchone()[0]

    approaching = cursor.execute("""
        SELECT COUNT(*) FROM fire_extinguishers
        WHERE (third_party_due_date BETWEEN ? AND ?)
        OR (monthly_due_date BETWEEN ? AND ?)
    """, (today, upcoming, today, upcoming)).fetchone()[0]

    total_products = cursor.execute("SELECT COUNT(*) FROM fire_extinguishers").fetchone()[0]

    type_summary = cursor.execute("""
        SELECT extinguisher_type, COUNT(*) as count
        FROM fire_extinguishers
        GROUP BY extinguisher_type
    """).fetchall()

    conn.close()

    labels = [row['extinguisher_type'] for row in type_summary]
    values = [row['count'] for row in type_summary]

    return render_template(
        'dashboard.html',
        overdue=overdue,
        approaching=approaching,
        total_products=total_products,
        upcoming_inspections=approaching,
        labels=labels,
        values=values
    )
#Fire Extinguisher Grupla basla
import sqlite3
from collections import defaultdict

# Bağlantıyı kur
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Verileri gruplu şekilde çek: location, type, capacity bazında sayım
cursor.execute("""
    SELECT location, extinguisher_type, capacity, COUNT(*) as total
    FROM fire_extinguishers
    GROUP BY location, extinguisher_type, capacity
""")
rows = cursor.fetchall()
conn.close()

# Yapıyı şu şekilde organize edelim: data[location][type][capacity] = adet
grouped_data = defaultdict(lambda: defaultdict(dict))
locations = set()
types = defaultdict(set)

for location, ext_type, capacity, total in rows:
    grouped_data[location][ext_type][capacity] = total
    locations.add(location)
    types[ext_type].add(capacity)

# Lokasyonları ve tip+kapasiteleri sıralanmış döndürelim
locations = sorted(locations)
types = {t: sorted(list(caps)) for t, caps in types.items()}

(locations, types, grouped_data)

@app.route('/extinguisher-summary')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def extinguisher_summary():
    from collections import defaultdict
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT location, extinguisher_type, capacity, COUNT(*) as total
        FROM fire_extinguishers
        GROUP BY location, extinguisher_type, capacity
    """)
    rows = cursor.fetchall()
    conn.close()

    # Gruplama
    grouped_data = defaultdict(lambda: defaultdict(dict))
    locations = set()
    types = defaultdict(set)

    for location, ext_type, capacity, total in rows:
        grouped_data[location][ext_type][capacity] = total
        locations.add(location)
        types[ext_type].add(capacity)

    locations = sorted(locations)
    types = {t: sorted(list(caps)) for t, caps in types.items()}

    return render_template(
        'extinguisher_summary.html',
        locations=locations,
        types=types,
        data=grouped_data
    )


#Fire Extinguisher Grupla son

#3rd Party Expirty Summary Table
@app.route('/extinguisher-monthly-summary')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def extinguisher_monthly_summary():
    from collections import defaultdict
    import calendar
    from datetime import datetime

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT location, third_party_due_date
        FROM fire_extinguishers
        WHERE third_party_due_date IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    summary = defaultdict(lambda: defaultdict(int))  # summary[location][month-year] = count
    locations = set()
    all_month_years = set()

    for location, due_date in rows:
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        elif isinstance(due_date, bytes):
            due_date = datetime.fromisoformat(due_date.decode())

        month_year = due_date.strftime("%b - %y")  # örnek: Jul - 26
        summary[location][month_year] += 1
        locations.add(location)
        all_month_years.add(month_year)

    # Ay-yıl etiketlerini sıralı hale getir
    def month_year_sort_key(label):
        return datetime.strptime(label, "%b - %y")

    sorted_month_labels = sorted(list(all_month_years), key=month_year_sort_key)
    locations = sorted(locations)

    return render_template(
        'extinguisher_monthly_summary.html',
        summary=summary,
        locations=locations,
        month_labels=sorted_month_labels
    )



#3rd Party Expirty Summary Table end






##### Yangin sondurucu ekle fire extinguishe add
@app.route('/add-fire-extinguisher', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def add_fire_extinguisher():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Dropdown için şirket listesini al
    companies = cursor.execute("SELECT id, company_name FROM companies ORDER BY company_name").fetchall()

    if request.method == 'POST':
        data = {
            'extinguisher_type': request.form['extinguisher_type'],
            'capacity': request.form['capacity'],
            'responsible_company_id': request.form['responsible_company_id'],
            'tag_number': request.form['tag_number'],
            'location': request.form['location'],
            'sub_location': request.form['sub_location'],
            'third_party_inspection_date': request.form['third_party_inspection_date'],
            'third_party_due_date': request.form['third_party_due_date'],
            'monthly_inspection_date': request.form['monthly_inspection_date'],
            'monthly_due_date': request.form['monthly_due_date'],
            'pressure_gauge': request.form['pressure_gauge'],
            'hose_nozzle': request.form['hose_nozzle'],
            'safety_pin': request.form['safety_pin'],
            'trigger': request.form['trigger'],
            'overall_condition': request.form['overall_condition'],
            'remarks': request.form['remarks']
        }

        try:
            cursor.execute("""
                INSERT INTO fire_extinguishers (
                    extinguisher_type, capacity, responsible_company_id, tag_number,
                    location, sub_location, third_party_inspection_date, third_party_due_date,
                    monthly_inspection_date, monthly_due_date, pressure_gauge, hose_nozzle,
                    safety_pin, trigger, overall_condition, remarks
                ) VALUES (
                    :extinguisher_type, :capacity, :responsible_company_id, :tag_number,
                    :location, :sub_location, :third_party_inspection_date, :third_party_due_date,
                    :monthly_inspection_date, :monthly_due_date, :pressure_gauge, :hose_nozzle,
                    :safety_pin, :trigger, :overall_condition, :remarks
                )
            """, data)

            conn.commit()
            flash("Fire extinguisher added successfully.", "success")
            return redirect(url_for('add_fire_extinguisher'))

        except sqlite3.IntegrityError:
            flash(f"Tag Number '{data['tag_number']}' is already in use. Please enter a unique Tag Number.", "danger")
            return render_template('add_fire_extinguisher.html', companies=companies, form=data)

        finally:
            conn.close()

    conn.close()
    return render_template('add_fire_extinguisher.html', companies=companies)
    ...

# Yangin sondurucu listesi fire extinguisher list

@app.route('/fire-extinguisher-list')
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def list_fire_extinguishers():
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)

    # 1. Yaklaşan veya geçmiş bakım tarihi olanlar
    due_extinguishers = cursor.execute("""
        SELECT fe.*, c.company_name
        FROM fire_extinguishers fe
        LEFT JOIN companies c ON fe.responsible_company_id = c.id
        WHERE
            (fe.third_party_due_date IS NOT NULL AND fe.third_party_due_date <= ?)
            OR
            (fe.monthly_due_date IS NOT NULL AND fe.monthly_due_date <= ?)
        ORDER BY fe.third_party_due_date ASC
    """, (upcoming, upcoming)).fetchall()

    # 2. Tüm fire extinguisher kayıtları
    all_extinguishers = cursor.execute("""
        SELECT fe.*, c.company_name
        FROM fire_extinguishers fe
        LEFT JOIN companies c ON fe.responsible_company_id = c.id
        ORDER BY fe.id DESC
    """).fetchall()

    # 3. Şirket listesi (PDF export filtreleri için)
    company_rows = cursor.execute("SELECT DISTINCT company_name FROM companies").fetchall()
    companies = []
    for row in company_rows:
        if row and 'company_name' in row.keys():
            companies.append(row['company_name'] or 'N/A')

    # 4. Lokasyon listesi (PDF export filtreleri için)
    location_rows = cursor.execute("SELECT DISTINCT location FROM fire_extinguishers").fetchall()
    locations = []
    for row in location_rows:
        if row and 'location' in row.keys():
            locations.append(row['location'] or 'Unknown')

    conn.close()

    return render_template(
        'fire_extinguisher_list.html',
        extinguishers=all_extinguishers,
        due_extinguishers=due_extinguishers,
        current_date=today,
        total=len(all_extinguishers),
        companies=companies,        # PDF export formunda kullanmak için
        locations=locations         # PDF export formunda kullanmak için
    )

# Yangin sondurucu listesi fire extinguisher list son

#from datetime import datetime

@app.template_filter('todate')
def todate(value):
    try:
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        return value
    except:
        return None

#Fire extinguisher summary pdf print
from collections import defaultdict

def get_extinguisher_summary_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, extinguisher_type, capacity, COUNT(*) as total
        FROM fire_extinguishers
        GROUP BY location, extinguisher_type, capacity
    """)
    rows = cursor.fetchall()
    conn.close()

    data = defaultdict(lambda: defaultdict(dict))
    locations = set()
    types = defaultdict(set)

    for location, ext_type, capacity, total in rows:
        data[location][ext_type][capacity] = total
        locations.add(location)
        types[ext_type].add(capacity)

    return sorted(locations), {t: sorted(list(caps)) for t, caps in types.items()}, data


@app.route('/extinguisher-summary-pdf')
def extinguisher_summary_pdf():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    import io, os
    from flask import send_file

    locations, types, data = get_extinguisher_summary_data()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=60, bottomMargin=30)
    elements = []

    def header_canvas(c, doc):
        logo_path = os.path.join("static", "Logo.jpg")
        if os.path.exists(logo_path):
            c.drawImage(ImageReader(logo_path), 30, doc.pagesize[1] - 60, width=100, height=35)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(doc.pagesize[0] / 2, doc.pagesize[1] - 40, "Fire Extinguisher Summary Table")

    # Başlık satırları
    top_header = ["NO", "LOCATION"]
    sub_header = ["", ""]
    col_keys = []
    group_spans = []

    for t, caps in types.items():
        top_header.extend([t] + [""] * (len(caps) - 1))
        sub_header.extend(caps)
        col_keys.extend([(t, c) for c in caps])
        group_spans.append((t, len(caps)))

    top_header.append("TOTAL")
    sub_header.append("")

    data_rows = [top_header, sub_header]

    grand_total = 0
    col_totals = [0 for _ in col_keys]

    for i, loc in enumerate(locations, start=1):
        row = [str(i), loc]
        row_total = 0
        for idx, (t, c) in enumerate(col_keys):
            val = int(data[loc][t].get(c, 0))
            row.append(str(val) if val > 0 else "")
            row_total += val
            col_totals[idx] += val
        row.append(str(row_total))
        grand_total += row_total
        data_rows.append(row)

    footer = ["TOTAL", ""]
    for val in col_totals:
        footer.append(str(val))
    footer.append(str(grand_total))
    data_rows.append(footer)

    # Genişlikler
    col_widths = [40, 80] + [50] * len(col_keys) + [60]

    # Tablo ve stil
    table = Table(data_rows, colWidths=col_widths)
    style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
        ('SPAN', (0, 0), (0, 1)),  # NO
        ('SPAN', (1, 0), (1, 1)),  # LOCATION
        ('SPAN', (-1, 0), (-1, 1)),  # TOTAL
    ])

    col_index = 2
    for group, span_count in group_spans:
        style.add('SPAN', (col_index, 0), (col_index + span_count - 1, 0))
        col_index += span_count

    table.setStyle(style)
    elements.append(table)
    doc.build(elements, onFirstPage=header_canvas, onLaterPages=header_canvas)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="FireExtinguisher_Summary.pdf", mimetype='application/pdf')


#Fire extinguisher summary pdf son







@app.route('/edit-fire-extinguisher/<int:extinguisher_id>', methods=['GET', 'POST'])
def update_fire_extinguisher(extinguisher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mevcut veri
    extinguisher = cursor.execute("SELECT * FROM fire_extinguishers WHERE id = ?", (extinguisher_id,)).fetchone()
    companies = cursor.execute("SELECT id, company_name FROM companies ORDER BY company_name").fetchall()

    if request.method == 'POST':
        cursor.execute("""
            UPDATE fire_extinguishers SET
                extinguisher_type = ?, capacity = ?, responsible_company_id = ?, tag_number = ?,
                location = ?, sub_location = ?, third_party_inspection_date = ?, third_party_due_date = ?,
                monthly_inspection_date = ?, monthly_due_date = ?, pressure_gauge = ?, hose_nozzle = ?,
                safety_pin = ?, trigger = ?, overall_condition = ?, remarks = ?
            WHERE id = ?
        """, (
            request.form['extinguisher_type'],
            request.form['capacity'],
            request.form['responsible_company_id'],
            request.form['tag_number'],
            request.form['location'],
            request.form['sub_location'],
            request.form['third_party_inspection_date'],
            request.form['third_party_due_date'],
            request.form['monthly_inspection_date'],
            request.form['monthly_due_date'],
            request.form['pressure_gauge'],
            request.form['hose_nozzle'],
            request.form['safety_pin'],
            request.form['trigger'],
            request.form['overall_condition'],
            request.form['remarks'],
            extinguisher_id
        ))
        conn.commit()
        conn.close()
        flash("Fire extinguisher updated successfully.", "success")
        return redirect(url_for('list_fire_extinguishers'))

    conn.close()
    return render_template('edit_fire_extinguisher.html', extinguisher=extinguisher, companies=companies)

@app.route('/edit-fire-extinguisher/<int:extinguisher_id>', methods=['GET', 'POST'])
def edit_fire_extinguisher(extinguisher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Şirketleri al (dropdown için)
    companies = cursor.execute("SELECT id, company_name FROM companies ORDER BY company_name").fetchall()

    # Mevcut yangın tüpü verilerini al
    extinguisher = cursor.execute("SELECT * FROM fire_extinguishers WHERE id = ?", (extinguisher_id,)).fetchone()

    if extinguisher is None:
        conn.close()
        flash("Fire extinguisher not found.", "danger")
        return redirect(url_for('list_fire_extinguishers'))

    if request.method == 'POST':
        updated_data = {
            'extinguisher_type': request.form['extinguisher_type'],
            'capacity': request.form['capacity'],
            'responsible_company_id': request.form['responsible_company_id'],
            'tag_number': request.form['tag_number'],
            'location': request.form['location'],
            'sub_location': request.form['sub_location'],
            'third_party_inspection_date': request.form['third_party_inspection_date'],
            'third_party_due_date': request.form['third_party_due_date'],
            'monthly_inspection_date': request.form['monthly_inspection_date'],
            'monthly_due_date': request.form['monthly_due_date'],
            'pressure_gauge': request.form['pressure_gauge'],
            'hose_nozzle': request.form['hose_nozzle'],
            'safety_pin': request.form['safety_pin'],
            'trigger': request.form['trigger'],
            'overall_condition': request.form['overall_condition'],
            'remarks': request.form['remarks'],
            'id': extinguisher_id
        }

        cursor.execute("""
            UPDATE fire_extinguishers SET
                extinguisher_type = :extinguisher_type,
                capacity = :capacity,
                responsible_company_id = :responsible_company_id,
                tag_number = :tag_number,
                location = :location,
                sub_location = :sub_location,
                third_party_inspection_date = :third_party_inspection_date,
                third_party_due_date = :third_party_due_date,
                monthly_inspection_date = :monthly_inspection_date,
                monthly_due_date = :monthly_due_date,
                pressure_gauge = :pressure_gauge,
                hose_nozzle = :hose_nozzle,
                safety_pin = :safety_pin,
                trigger = :trigger,
                overall_condition = :overall_condition,
                remarks = :remarks
            WHERE id = :id
        """, updated_data)

        conn.commit()
        conn.close()
        flash("Fire extinguisher updated successfully.", "success")
        return redirect(url_for('list_fire_extinguishers'))

    conn.close()
    return render_template('edit_fire_extinguisher.html', extinguisher=extinguisher, companies=companies)


from dateutil.relativedelta import relativedelta

from flask import request, render_template, flash
import pandas as pd
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils import normalize_result


#### Upload Bulk Fire Extingusher

from dateutil.relativedelta import relativedelta
from flask import request, render_template, flash
import pandas as pd
import sqlite3
from datetime import datetime
from utils import normalize_result

@app.route('/upload-fire-extinguisher', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector')  # sadece bu roller erişebilir
def upload_fire_extinguisher():
    if request.method == 'POST':
        file = request.files['excel_file']
        if file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
                df['third_party_inspection_date'] = pd.to_datetime(df['third_party_inspection_date'], dayfirst=True, errors='coerce')
                df['monthly_inspection_date'] = pd.to_datetime(df['monthly_inspection_date'], dayfirst=True, errors='coerce')

                inserted_records = []

                with sqlite3.connect(DB_FILE, timeout=10) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()

                    for _, row in df.iterrows():
                        try:
                            cursor.execute("SELECT id FROM companies WHERE company_name = ?", (row['responsible_company'],))
                            company = cursor.fetchone()
                            responsible_company_id = company['id'] if company else None
                            if not responsible_company_id:
                                continue

                            tpi_date = row['third_party_inspection_date']
                            mpi_date = row['monthly_inspection_date']
                            if pd.isnull(tpi_date) and pd.isnull(mpi_date):
                                continue

                            third_due = tpi_date + relativedelta(years=1) if pd.notnull(tpi_date) else None
                            monthly_due = mpi_date + relativedelta(months=1) if pd.notnull(mpi_date) else None

                            pg = normalize_result(row['pressure_gauge'])
                            hn = normalize_result(row['hose_nozzle'])
                            sp = normalize_result(row['safety_pin'])
                            tr = normalize_result(row['trigger'])

                            if str(row['extinguisher_type']).strip().upper() == 'CO2':
                                pg = 'N/A'

                            cursor.execute("SELECT id FROM fire_extinguishers WHERE tag_number = ?", (row['tag_number'],))
                            existing = cursor.fetchone()

                            if existing:
                                cursor.execute("""
                                    UPDATE fire_extinguishers
                                    SET extinguisher_type = ?, capacity = ?, responsible_company_id = ?,
                                        location = ?, sub_location = ?, third_party_inspection_date = ?, third_party_due_date = ?,
                                        monthly_inspection_date = ?, monthly_due_date = ?, pressure_gauge = ?, hose_nozzle = ?,
                                        safety_pin = ?, trigger = ?, overall_condition = ?, remarks = ?
                                    WHERE tag_number = ?
                                """, (
                                    row['extinguisher_type'], row['capacity'], responsible_company_id,
                                    row['location'], row.get('sub_location', ''),
                                    tpi_date.strftime('%Y-%m-%d') if pd.notnull(tpi_date) else None,
                                    third_due.strftime('%Y-%m-%d') if third_due else None,
                                    mpi_date.strftime('%Y-%m-%d') if pd.notnull(mpi_date) else None,
                                    monthly_due.strftime('%Y-%m-%d') if monthly_due else None,
                                    pg, hn, sp, tr,
                                    row['overall_condition'], row.get('remarks', ''),
                                    row['tag_number']
                                ))
                            else:
                                cursor.execute("""
                                    INSERT INTO fire_extinguishers (
                                        extinguisher_type, capacity, responsible_company_id, tag_number,
                                        location, sub_location, third_party_inspection_date, third_party_due_date,
                                        monthly_inspection_date, monthly_due_date, pressure_gauge, hose_nozzle,
                                        safety_pin, trigger, overall_condition, remarks
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    row['extinguisher_type'], row['capacity'], responsible_company_id, row['tag_number'],
                                    row['location'], row.get('sub_location', ''),
                                    tpi_date.strftime('%Y-%m-%d') if pd.notnull(tpi_date) else None,
                                    third_due.strftime('%Y-%m-%d') if third_due else None,
                                    mpi_date.strftime('%Y-%m-%d') if pd.notnull(mpi_date) else None,
                                    monthly_due.strftime('%Y-%m-%d') if monthly_due else None,
                                    pg, hn, sp, tr,
                                    row['overall_condition'], row.get('remarks', '')
                                ))

                            inserted_records.append({
                                "type": row['extinguisher_type'],
                                "capacity": row['capacity'],
                                "company": row['responsible_company'],
                                "tag": row['tag_number'],
                                "location": row['location']
                            })
                        except Exception as row_err:
                            print("SKIP - Error inserting/updating row:", row.to_dict(), "| Reason:", str(row_err))

                    conn.commit()

                if not inserted_records:
                    flash("No records were added. Check company names and required fields.", "warning")
                return render_template('upload_summary.html', records=inserted_records)

            except Exception as e:
                flash(f"Error processing file: {str(e)}", 'danger')
        else:
            flash('Invalid file type. Please upload an .xlsx file.', 'warning')

    return render_template('upload_fire_extinguisher.html')




#### Upload Bulk Fire Extingusher - Son




@app.route('/inspect-fire-extinguisher/<int:extinguisher_id>', methods=['GET', 'POST'])
def inspect_fire_extinguisher(extinguisher_id):
    from datetime import datetime

    def normalize_result(val):
        val = str(val).strip().lower()
        return 'Pass' if val in ['pass', 'passed', 'yes', 'ok'] else 'Fail'

    if request.method == 'POST':
        pressure_gauge = normalize_result(request.form.get('pressure_gauge'))
        hose_nozzle = normalize_result(request.form.get('hose_nozzle'))
        safety_pin = normalize_result(request.form.get('safety_pin'))
        trigger = normalize_result(request.form.get('trigger'))
        overall_condition = request.form.get('overall_condition')
        remarks = request.form.get('remarks')

        # Tarihleri kontrol et
        def parse_date(field_name):
            val = request.form.get(field_name)
            return datetime.strptime(val, "%Y-%m-%d").strftime("%Y-%m-%d") if val else None

        third_party_inspection_date = parse_date('third_party_inspection_date')
        third_party_due_date = parse_date('third_party_due_date')
        monthly_inspection_date = parse_date('monthly_inspection_date')
        monthly_due_date = parse_date('monthly_due_date')

        with sqlite3.connect(DB_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE fire_extinguishers
                SET pressure_gauge = ?, hose_nozzle = ?, safety_pin = ?, trigger = ?, overall_condition = ?,
                    third_party_inspection_date = ?, third_party_due_date = ?,
                    monthly_inspection_date = ?, monthly_due_date = ?,
                    remarks = ?
                WHERE id = ?
            ''', (
                pressure_gauge, hose_nozzle, safety_pin, trigger, overall_condition,
                third_party_inspection_date, third_party_due_date,
                monthly_inspection_date, monthly_due_date,
                remarks, extinguisher_id
            ))
            conn.commit()

        flash("Inspection updated successfully.", "success")
        return redirect(url_for('list_fire_extinguishers'))

    # GET: veri çek
    with sqlite3.connect(DB_FILE, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        extinguisher = conn.execute('SELECT * FROM fire_extinguishers WHERE id = ?', (extinguisher_id,)).fetchone()

    if not extinguisher:
        flash("Fire extinguisher not found.", "danger")
        return redirect(url_for('list_fire_extinguishers'))

    return render_template('inspect_fire_extinguisher.html', extinguisher=extinguisher)


from flask import request, redirect, url_for, flash
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta



@app.route('/bulk_inspect_fire_extinguishers', methods=['POST'])
def bulk_inspect_fire_extinguishers():
    selected_ids = request.form.getlist('selected_ids')
    if not selected_ids:
        flash("No extinguishers selected.", "warning")
        return redirect(url_for('list_fire_extinguishers'))

    # Formdan gelen veriler
    pg_raw = request.form.get('bulk_pressure_gauge')
    hn_raw = request.form.get('bulk_hose_nozzle')
    sp_raw = request.form.get('bulk_safety_pin')
    tr_raw = request.form.get('bulk_trigger')
    monthly_inspection_date = request.form.get('bulk_inspection_date')
    third_party_inspection_date = request.form.get('bulk_third_party_inspection_date')
    remarks = request.form.get('bulk_remarks')

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for extinguisher_id in selected_ids:
            cursor.execute("SELECT extinguisher_type FROM fire_extinguishers WHERE id = ?", (extinguisher_id,))
            row = cursor.fetchone()
            if not row:
                continue

            extinguisher_type = row['extinguisher_type'].strip().upper()

            # CO₂ tipi için pressure_gauge = N/A
            pg = 'N/A' if extinguisher_type == 'CO2' else normalize_result(pg_raw)
            hn = normalize_result(hn_raw)
            sp = normalize_result(sp_raw)
            tr = normalize_result(tr_raw)

            # Tarih ve due date işlemleri
            mpi_date = monthly_inspection_date
            tpi_date = third_party_inspection_date
            monthly_due = ''
            third_due = ''

            if mpi_date:
                try:
                    mpi_dt = datetime.strptime(mpi_date, '%Y-%m-%d')
                    monthly_due = (mpi_dt + relativedelta(months=1)).strftime('%Y-%m-%d')
                except:
                    mpi_date = None

            if tpi_date:
                try:
                    tpi_dt = datetime.strptime(tpi_date, '%Y-%m-%d')
                    third_due = (tpi_dt + relativedelta(years=1)).strftime('%Y-%m-%d')
                except:
                    tpi_date = None

            cursor.execute("""
                UPDATE fire_extinguishers
                SET pressure_gauge = ?, hose_nozzle = ?, safety_pin = ?, trigger = ?,
                    monthly_inspection_date = ?, monthly_due_date = ?,
                    third_party_inspection_date = ?, third_party_due_date = ?,
                    remarks = ?
                WHERE id = ?
            """, (
                pg, hn, sp, tr,
                mpi_date, monthly_due,
                tpi_date, third_due,
                remarks,
                extinguisher_id
            ))

        conn.commit()

    flash("Bulk inspection update applied successfully.", "success")
    return redirect(url_for('list_fire_extinguishers'))



@app.route('/export-fire-extinguishers-pdf')
def export_fire_extinguishers_pdf():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from datetime import datetime
    import io, sqlite3, os
    from flask import request, send_file

    # 🔎 Filtre alınır
    company = request.args.get('company')
    location = request.args.get('location')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()
    elements = []

    # 📌 Logo ve başlık
    logo_path = os.path.join("static", "Logo.jpg")
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=35))

    title = "FIRE EXTINGUISHER INSPECTION LIST"
    if company:
        title += f" - Company: {company}"
    elif location:
        title += f" - Location: {location}"

    elements.append(Paragraph(f"<b>{title}</b>", styles['Title']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Exported on: {datetime.now().strftime('%d-%b-%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # 🔗 Veritabanı sorgusu
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    query = """
        SELECT fe.tag_number, fe.extinguisher_type, fe.capacity, fe.location, fe.sub_location,
               fe.third_party_inspection_date, fe.third_party_due_date,
               fe.monthly_inspection_date, fe.monthly_due_date,
               fe.pressure_gauge, fe.hose_nozzle, fe.safety_pin, fe.trigger, fe.remarks
        FROM fire_extinguishers fe
        JOIN companies c ON fe.responsible_company_id = c.id
    """
    filters = []
    params = []

    if company:
        filters.append("c.company_name = ?")
        params.append(company)
    if location:
        filters.append("fe.location = ?")
        params.append(location)

    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY fe.tag_number"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # 📄 Veri hazırlanır, CO2 için özel işlem yapılır
    header = ["No", "Tag", "Type", "Capacity", "Location", "Sub-Location", "3rd Party Insp.", "3rd Party Due",
              "Monthly Insp.", "Monthly Due", "Pressure", "Hose", "Pin", "Trigger", "Remarks"]
    data = [header]

    for i, row in enumerate(rows, start=1):
        (
            tag, etype, cap, loc, subloc,
            tpi, tpd, mpi, mpd,
            pressure, hose, pin, trig, rem
        ) = row

        # CO2 için Pressure Gauge değeri "N/A" olarak ayarlanır
        if etype == 'CO2':
            pressure = 'N/A'

        data.append([
            str(i), tag, etype, cap, loc, subloc,
            tpi or '-', tpd or '-', mpi or '-', mpd or '-',
            pressure, hose, pin, trig, rem
        ])

    # 🧾 Tablo oluşturulur
    table = Table(data, repeatRows=1, hAlign='CENTER', colWidths=[
        25, 55, 45, 45, 55, 65, 60, 60, 60, 60, 40, 40, 40, 40, 85
    ])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    elements.append(table)

    # ✍️ İmza alanı
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Inspector Signature: ____________________", styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Date: ____________________", styles['Normal']))

    # 📄 Sayfa numarası
    def add_page_number(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(285 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    filename = f"Fire_Extinguishers_{company or location or 'All'}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")



@app.route('/export-fire-extinguishers-excel')
def export_fire_extinguishers_excel():
    import pandas as pd
    import io
    from flask import send_file

    conn = get_db_connection()
    query = """
        SELECT
            fe.tag_number, fe.extinguisher_type, fe.capacity,
            c.company_name AS responsible_company,
            fe.location, fe.sub_location,
            fe.third_party_inspection_date, fe.third_party_due_date,
            fe.monthly_inspection_date, fe.monthly_due_date,
            fe.pressure_gauge, fe.hose_nozzle, fe.safety_pin,
            fe.trigger, fe.overall_condition, fe.remarks
        FROM fire_extinguishers fe
        LEFT JOIN companies c ON fe.responsible_company_id = c.id
        ORDER BY fe.location, fe.tag_number
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Fire Extinguishers")

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="Fire_Extinguisher_List.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )





@app.route('/edit-brand/<int:brand_id>', methods=['GET', 'POST'])
def edit_brand(brand_id):
    conn = get_db_connection()
    brand = conn.execute('SELECT * FROM brands WHERE id = ?', (brand_id,)).fetchone()

    if request.method == 'POST':
        new_name = request.form['name']
        conn.execute('UPDATE brands SET name = ? WHERE id = ?', (new_name, brand_id))
        conn.commit()
        conn.close()
        return redirect(url_for('add_brand'))

    conn.close()
    return render_template('edit_brand.html', brand=brand)

@app.route('/delete-brand/<int:brand_id>', methods=['POST'])
def delete_brand(brand_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM brands WHERE id = ?', (brand_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('add_brand'))


def sync_users_from_assignments():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO users (badge_number, full_name)
        SELECT badge_number, MIN(assigned_to)
        FROM assignments
        WHERE badge_number IS NOT NULL
        GROUP BY badge_number
    ''')

    conn.commit()
    conn.close()
    print("✅ users tablosu başarıyla senkronize edildi.")


# ===================== DB İşlemleri =====================
def generate_tags_and_save(n):
    start = get_last_tag_number() + 1
    with sqlite3.connect(DB_FILE) as conn:
        for i in range(start, start + n):
            tag = f"FE-{i:04d}"
            qr_url = tag
            conn.execute("INSERT INTO cards (tag, qr_url) VALUES (?, ?)", (tag, qr_url))
        conn.commit()

def get_last_tag_number():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tag FROM cards ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return int(row[0].split('-')[1])
        return 0


#manual scan fire extinguisher

@app.route('/manual-scan', methods=['GET', 'POST'])
def manual_scan():
    tag = request.args.get('tag')
    print("DEBUG: Scanned tag ->", tag)

    if request.method == 'POST':
        # Form gönderildiyse, işlem yap ve manuel tarama sayfasına geri dön
        flash("✅ Inspection submitted successfully.", "success")
        return redirect(url_for('manual_scan'))

    if not tag:
        return render_template('manual_scan_fire.html', extinguisher=None, readonly=True, tag=None)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fire_extinguishers WHERE tag_number = ?", (tag,))
    extinguisher = cursor.fetchone()
    conn.close()

    if extinguisher is None:
        flash("No extinguisher found with this tag.", "danger")
        return redirect(url_for('manual_scan'))

    readonly = 'username' not in session


    flash(f"Inspection for {tag} saved successfully.", "success")
    return render_template(
        'manual_scan_fire.html',
        tag=tag,
        extinguisher=extinguisher,
        readonly=readonly
    )


from flask import request, render_template


###### fire extinguisher inspection form
# inspect_tag route (Python)
@app.route('/inspect-tag/<tag>', methods=['GET', 'POST'])
def inspect_tag(tag):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 🔍 Extinguisher verisini al
    cursor.execute("SELECT * FROM fire_extinguishers WHERE tag_number = ?", (tag,))
    extinguisher = cursor.fetchone()

    if not extinguisher:
        conn.close()
        flash("No extinguisher found with this tag.", "danger")
        return redirect(url_for('manual_scan'))

    # 🔒 Login kontrolü
    show_form = 'username' in session

    if request.method == 'POST':
        if not show_form:
            flash("You must be logged in to perform inspection.", "danger")
            return redirect(url_for('login'))

        def normalize_result(val):
            if val:
                val = str(val).strip().lower()
                return 'Pass' if val in ['pass', 'passed', 'yes', 'ok'] else 'Fail'
            return None

        # 📝 Formdan gelen değerler
        pressure_gauge = normalize_result(request.form.get('pressure_gauge'))
        hose_nozzle = normalize_result(request.form.get('hose_nozzle'))
        safety_pin = normalize_result(request.form.get('safety_pin'))
        trigger = normalize_result(request.form.get('trigger'))
        overall_condition = request.form.get('overall_condition')
        remarks = request.form.get('remarks')

        # 🔹 1. Geçmiş log'a INSERT
        cursor.execute('''
            INSERT INTO fire_extinguisher_inspections (
                extinguisher_id, pressure_gauge, hose_nozzle, safety_pin,
                trigger, overall_condition, remarks, date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'))
        ''', (
            extinguisher['id'], pressure_gauge, hose_nozzle, safety_pin,
            trigger, overall_condition, remarks
        ))

        # 🔹 2. fire_extinguishers tablosunu UPDATE et
        cursor.execute('''
            UPDATE fire_extinguishers
            SET pressure_gauge = ?, hose_nozzle = ?, safety_pin = ?,
                trigger = ?, overall_condition = ?, remarks = ?
            WHERE id = ?
        ''', (
            pressure_gauge, hose_nozzle, safety_pin,
            trigger, overall_condition, remarks, extinguisher['id']
        ))

        conn.commit()
        flash("Inspection submitted successfully.", "success")
        return redirect(url_for('inspect_tag', tag=tag))

    # 📜 Son 5 inspection geçmişi
    cursor.execute("""
        SELECT * FROM fire_extinguisher_inspections
        WHERE extinguisher_id = ?
        ORDER BY date DESC LIMIT 5
    """, (extinguisher['id'],))
    inspections = cursor.fetchall()
    conn.close()

    # 📱 Mobil mi masaüstü mü kontrolü
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(x in user_agent for x in ['android', 'iphone', 'ipad', 'mobile'])

    # 👁️ Doğru template'i seç
    template = 'inspect_fire_extinguisher_mobile.html' if is_mobile else 'inspect_fire_extinguisher.html'

    return render_template(template,
                           tag=tag,
                           extinguisher=extinguisher,
                           inspections=inspections,
                           show_form=show_form)








# ===================== PDF Oluşturma =====================
def draw_card(c, x, y, tag, qr_url):
    card_w, card_h = 42 * mm, 50 * mm  # daha küçük kart
    c.roundRect(x, y, card_w, card_h, 2 * mm)

    # Başlık
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + card_w / 2, y + card_h - 6 * mm, "JV NPCC-SAIPEM")

    # TAG
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + card_w / 2, y + card_h - 13 * mm, tag)

    # QR Görsel
    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    qr_img = ImageReader(buffer)

    c.drawImage(qr_img, x + (card_w - 24 * mm) / 2, y + 5 * mm, width=24 * mm, height=24 * mm)


def generate_pdfs(count):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tag, qr_url FROM cards ORDER BY id DESC LIMIT ?", (count,))
        records = cursor.fetchall()[::-1]

    # Sayfa başına 20 kart (4 sütun x 5 satır)
    cards_per_page = 20
    pages = [records[i:i + cards_per_page] for i in range(0, len(records), cards_per_page)]
    pdf_paths = []

    for idx, page in enumerate(pages):
        pdf_path = os.path.join(OUTPUT_FOLDER, f"cards_page_{idx+1}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        page_w, page_h = A4

        # Küçük kart ölçüleri
        card_w, card_h = 42 * mm, 50 * mm
        cols = 4
        rows = 5

        spacing_x = (page_w - (cols * card_w)) / (cols + 1)
        spacing_y = (page_h - (rows * card_h)) / (rows + 1)

        for i, (tag, qr_url) in enumerate(page):
            row = i // cols
            col = i % cols
            x = spacing_x + col * (card_w + spacing_x)
            y = page_h - ((row + 1) * card_h + (row + 1) * spacing_y)
            draw_card(c, x, y, tag, qr_url)

        c.save()
        pdf_paths.append(pdf_path)

    return pdf_paths

# ===================== Web Sayfası =====================

@app.route('/generate-tags', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'inspector') # sadece bu roller erişebilir
def generate_tags():
    if request.method == 'POST':
        try:
            count = int(request.form['quantity'])
            if count <= 0 or count > 100:
                flash("Please enter a number between 1 and 100.", "warning")
                return redirect(url_for('generate_tags'))
        except:
            flash("Invalid input.", "danger")
            return redirect(url_for('generate_tags'))

        generate_tags_and_save(count)
        pdf_paths = generate_pdfs(count)
        if not pdf_paths or not os.path.exists(pdf_paths[0]):
            flash("PDF creation failed.", "danger")
            return redirect(url_for('generate_tags'))

        return send_file(pdf_paths[0], as_attachment=True)

    return render_template('generate_tags.html')


@app.route('/generate-scba-tags', methods=['POST'])
@login_required
def generate_scba_tags():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from io import BytesIO
    import qrcode
    import sqlite3
    import os

    qty = int(request.form['scba_quantity'])
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT tag_number FROM scba_units WHERE tag_number LIKE 'SCBA-%' ORDER BY tag_number DESC LIMIT 1")
    last_tag = cursor.fetchone()
    last_num = int(last_tag['tag_number'].split('-')[-1]) if last_tag else 0

    new_tags = []
    for i in range(1, qty + 1):
        num = last_num + i
        tag = f"SCBA-{num:04d}"
        new_tags.append(tag)
        cursor.execute("""
            INSERT INTO scba_units (tag_number, brand, model, cylinder_capacity, cylinder_pressure)
            VALUES (?, '', '', '', '')
        """, (tag,))

    conn.commit()
    conn.close()

    # === PDF Oluşturma ===
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4

    card_w, card_h = 42 * mm, 50 * mm
    cols, rows = 4, 5
    spacing_x = (page_w - (cols * card_w)) / (cols + 1)
    spacing_y = (page_h - (rows * card_h)) / (rows + 1)

    for i, tag in enumerate(new_tags):
        row = i // cols
        col = i % cols
        if row >= rows:
            c.showPage()
            row = 0
            col = 0

        x = spacing_x + col * (card_w + spacing_x)
        y = page_h - ((row + 1) * card_h + (row + 1) * spacing_y)

        # --- Kart çizimi ---
        c.roundRect(x, y, card_w, card_h, 2 * mm)

        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + card_w / 2, y + card_h - 6 * mm, "JV NPCC-SAIPEM")

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + card_w / 2, y + card_h - 13 * mm, tag)

        qr = qrcode.make(tag)
        qr_buffer = BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_img = ImageReader(qr_buffer)
        c.drawImage(qr_img, x + (card_w - 24 * mm) / 2, y + 5 * mm, width=24 * mm, height=24 * mm)

    c.save()

    # PDF çıktısı döndür
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='scba_qr_cards.pdf', mimetype='application/pdf')




# ===================== inspection tag =====================

@app.route('/inspect-desktop/<int:extinguisher_id>', methods=['GET', 'POST'])
def inspect_fire_extinguisher_desktop(extinguisher_id):
    from datetime import datetime
    conn = get_db_connection()
    cursor = conn.cursor()

    # Söndürücüyü getir
    extinguisher = cursor.execute(
        "SELECT * FROM fire_extinguishers WHERE id = ?", (extinguisher_id,)
    ).fetchone()

    if not extinguisher:
        conn.close()
        flash("Fire extinguisher not found.", "danger")
        return redirect(url_for('list_fire_extinguishers'))

    if request.method == 'POST':
        pressure_gauge = request.form.get('pressure_gauge')
        hose_nozzle = request.form.get('hose_nozzle')
        safety_pin = request.form.get('safety_pin')
        trigger = request.form.get('trigger')
        overall_condition = request.form.get('overall_condition')
        remarks = request.form.get('remarks')

        # Tarihler
        third_party_inspection_date = request.form.get('third_party_inspection_date')
        monthly_inspection_date = request.form.get('monthly_inspection_date')
        now = datetime.now()

        # Sonraki tarihler
        from dateutil.relativedelta import relativedelta
        third_due = (datetime.strptime(third_party_inspection_date, "%Y-%m-%d") + relativedelta(years=1)).strftime("%Y-%m-%d") if third_party_inspection_date else None
        monthly_due = (datetime.strptime(monthly_inspection_date, "%Y-%m-%d") + relativedelta(months=1)).strftime("%Y-%m-%d") if monthly_inspection_date else None

        # Güncelleme
        cursor.execute("""
            UPDATE fire_extinguishers
            SET pressure_gauge = ?, hose_nozzle = ?, safety_pin = ?, trigger = ?, overall_condition = ?,
                remarks = ?, third_party_inspection_date = ?, third_party_due_date = ?,
                monthly_inspection_date = ?, monthly_due_date = ?
            WHERE id = ?
        """, (
            pressure_gauge, hose_nozzle, safety_pin, trigger, overall_condition,
            remarks, third_party_inspection_date, third_due,
            monthly_inspection_date, monthly_due,
            extinguisher_id
        ))

        conn.commit()
        conn.close()
        flash("Inspection updated successfully.", "success")
        return redirect(url_for('list_fire_extinguishers'))

    conn.close()
    return render_template("inspect_fire_extinguisher_desktop.html", extinguisher=extinguisher)


@app.route('/inspect-tag/<tag>', methods=['GET', 'POST'])
def inspect_fire_extinguisher_mobile(tag):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import sqlite3

    tag = tag.strip().upper()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    extinguisher = cursor.execute(
        "SELECT * FROM fire_extinguishers WHERE UPPER(tag_number) = ?", (tag,)
    ).fetchone()

    if not extinguisher:
        conn.close()
        return f"<h3>❌ Tag '{tag}' not found in the system.</h3>"

    extinguisher_id = extinguisher['id']

    inspections = cursor.execute("""
        SELECT date, pressure_gauge, hose_nozzle, safety_pin, trigger, overall_condition, remarks
        FROM fire_extinguisher_inspections
        WHERE extinguisher_id = ?
        ORDER BY date DESC
        LIMIT 5
    """, (extinguisher_id,)).fetchall()

    show_form = 'user' in session

    if request.method == 'POST' and show_form:
        pressure_gauge = request.form.get('pressure_gauge')
        hose_nozzle = request.form.get('hose_nozzle')
        safety_pin = request.form.get('safety_pin')
        trigger = request.form.get('trigger')
        overall_condition = request.form.get('overall_condition')
        remarks = request.form.get('remarks')

        now = datetime.now().strftime("%Y-%m-%d")
        monthly_due = (datetime.now() + relativedelta(months=1)).strftime("%Y-%m-%d")

        try:
            # Güncelleme
            cursor.execute('''
                UPDATE fire_extinguishers SET
                    pressure_gauge = ?, hose_nozzle = ?, safety_pin = ?, trigger = ?,
                    overall_condition = ?, monthly_inspection_date = ?, monthly_due_date = ?,
                    remarks = ?
                WHERE id = ?
            ''', (
                pressure_gauge, hose_nozzle, safety_pin, trigger,
                overall_condition, now, monthly_due, remarks, extinguisher_id
            ))

            # Yeni inspection ekle
            cursor.execute("""
                INSERT INTO fire_extinguisher_inspections (
                    extinguisher_id, date, pressure_gauge, hose_nozzle,
                    safety_pin, trigger, overall_condition, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                extinguisher_id, now, pressure_gauge, hose_nozzle,
                safety_pin, trigger, overall_condition, remarks
            ))

            conn.commit()
            conn.close()
            return redirect(url_for('manual_scan'))  # 🔁 Mobilde tekrar QR okutma sayfasına dön
        except Exception as e:
            conn.close()
            return f"<h3>❌ Error occurred: {e}</h3>"

    conn.close()
    return render_template(
        'inspect_mobile.html',
        tag=tag,
        extinguisher=extinguisher,
        inspections=inspections,
        show_form=show_form
    )


@app.route('/auth-users')
@login_required
@role_required('admin')
def auth_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM auth_users").fetchall()
    conn.close()
    return render_template('auth_users.html', users=users)

@app.route('/add-auth-user', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_auth_user():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        role = request.form['role']
        password = request.form['password']

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO auth_users (username, full_name, role, password) VALUES (?, ?, ?, ?)",
                       (username, full_name, role, hashed))
        conn.commit()
        conn.close()

        flash("New user added!", "success")
        return redirect(url_for('auth_users'))

    return render_template('add_auth_user.html')

@app.route('/delete-auth-user/<int:user_id>')
@login_required
@role_required('admin')
def delete_auth_user(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM auth_users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted.", "warning")
    return redirect(url_for('auth_users'))

@app.route('/update-auth-password/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # Sadece admin güncelleyebilir
def update_auth_password(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, full_name, role FROM auth_users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('list_auth_users'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(request.url)

        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("UPDATE auth_users SET password = ? WHERE id = ?", (hashed, user_id))
        conn.commit()
        conn.close()

        flash("Password updated successfully.", "success")
        return redirect(url_for('list_auth_users'))

    conn.close()
    return render_template('update_auth_password.html', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user_id = session.get('user_id')

    if request.method == 'POST':
        current_password = request.form['current_password'].encode('utf-8')
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM auth_users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(current_password, user['password']):
            if new_password != confirm_password:
                flash("New passwords do not match.", "warning")
                return redirect(url_for('change_password'))

            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE auth_users SET password = ? WHERE id = ?", (hashed, user_id))
            conn.commit()
            conn.close()
            flash("Password changed successfully.", "success")
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('change_password'))

    return render_template('change_password.html')


@app.route('/thanks/<tag>')
def thanks(tag):
    return render_template('thanks.html', tag=tag)



with app.app_context():
    print(app.url_map)







# if __name__ == '__main__':
  #   sync_users_from_assignments()  # 👈 bu satırı bir kez çağır
    # app.run(debug=True)
