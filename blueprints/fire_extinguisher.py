from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, timedelta
import sqlite3, pandas as pd, io

fire_extinguisher_bp = Blueprint('fire_extinguisher_bp', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

@fire_extinguisher_bp.route('/add-fire-extinguisher', methods=['GET', 'POST'])
def add_fire_extinguisher():
    conn = get_db_connection()
    cursor = conn.cursor()
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
        except sqlite3.IntegrityError:
            flash("Error: Tag number already exists.", "danger")
        finally:
            conn.close()

        return redirect(url_for('fire_extinguisher_bp.add_fire_extinguisher'))

    conn.close()
    return render_template('fire_extinguishers/add_fire_extinguisher.html', companies=companies)

@fire_extinguisher_bp.route('/fire-extinguisher-list')
def list_fire_extinguishers():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)

    due_extinguishers = [
        dict(fe) for fe in cursor.execute("""
            SELECT fe.*, c.company_name
            FROM fire_extinguishers fe
            LEFT JOIN companies c ON fe.responsible_company_id = c.id
            WHERE 
                (fe.third_party_due_date IS NOT NULL AND fe.third_party_due_date <= ?)
                OR
                (fe.monthly_due_date IS NOT NULL AND fe.monthly_due_date <= ?)
            ORDER BY fe.third_party_due_date ASC
        """, (upcoming, upcoming)).fetchall()
    ]

    all_extinguishers = [
        dict(fe) for fe in cursor.execute("""
            SELECT fe.*, c.company_name
            FROM fire_extinguishers fe
            LEFT JOIN companies c ON fe.responsible_company_id = c.id
            ORDER BY fe.id DESC
        """).fetchall()
    ]

    conn.close()

    for fe in due_extinguishers:
        fe['third_party_due_date'] = parse_date(fe['third_party_due_date'])
        fe['monthly_due_date'] = parse_date(fe['monthly_due_date'])

    for fe in all_extinguishers:
        fe['third_party_due_date'] = parse_date(fe['third_party_due_date'])
        fe['monthly_due_date'] = parse_date(fe['monthly_due_date'])

    return render_template('fire_extinguishers/fire_extinguisher_list.html',
                           extinguishers=all_extinguishers,
                           due_extinguishers=due_extinguishers,
                           current_date=today)

@fire_extinguisher_bp.route('/fire-extinguisher-matrix')
def fire_extinguisher_matrix():
    return render_template('fire_extinguishers/matrix_placeholder.html')





@fire_extinguisher_bp.route('/upload-fire-extinguisher', methods=['GET', 'POST'])
def upload_fire_extinguisher():
    if request.method == 'POST':
        file = request.files['excel_file']
        if file.filename.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)
                conn = get_db_connection()
                cursor = conn.cursor()
                inserted_records = []

                for _, row in df.iterrows():
                    cursor.execute("SELECT id FROM companies WHERE company_name = ?", (row['responsible_company'],))
                    company = cursor.fetchone()
                    responsible_company_id = company['id'] if company else None
                    if not responsible_company_id:
                        continue

                    cursor.execute("""
                        INSERT INTO fire_extinguishers (
                            extinguisher_type, capacity, responsible_company_id, tag_number,
                            location, sub_location, third_party_inspection_date, third_party_due_date,
                            monthly_inspection_date, monthly_due_date, pressure_gauge, hose_nozzle,
                            safety_pin, trigger, overall_condition, remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, DATE(?, '+1 year'), ?, DATE(?, '+30 day'), ?, ?, ?, ?, ?, ?)
                    """, (
                        row['extinguisher_type'], row['capacity'], responsible_company_id, row['tag_number'],
                        row['location'], row.get('sub_location', ''),
                        row['third_party_inspection_date'], row['third_party_inspection_date'],
                        row['monthly_inspection_date'], row['monthly_inspection_date'],
                        row['pressure_gauge'], row['hose_nozzle'], row['safety_pin'],
                        row['trigger'], row['overall_condition'], row.get('remarks', '')
                    ))

                    inserted_records.append({
                        "type": row['extinguisher_type'],
                        "capacity": row['capacity'],
                        "company": row['responsible_company'],
                        "tag": row['tag_number'],
                        "location": row['location']
                    })

                conn.commit()
                conn.close()
                return render_template('fire_extinguishers/upload_summary.html', records=inserted_records)

            except Exception as e:
                flash(f"Error processing file: {str(e)}", 'danger')
        else:
            flash('Invalid file type. Please upload an .xlsx file.', 'warning')

    return render_template('fire_extinguishers/upload_fire_extinguisher.html')
