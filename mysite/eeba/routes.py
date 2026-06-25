# eeba/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import sqlite3, io, os
from pathlib import Path
import pandas as pd
from datetime import datetime

DB_PATH = Path("/home/mytestapp/mysite/database.db")
UPLOAD_MAX_MB = 10
ALLOWED_EXT = {".xlsx"}

eeba_bp = Blueprint("eeba_bp", __name__, url_prefix="/eeba")

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

# ---------- Add EEBA ----------
@eeba_bp.route("/add", methods=["GET","POST"])
def add_eeba():
    if request.method == "POST":
        f = request.form

        # TAG NO normalize: boşlukları kırp, büyük harf yap
        tag = (f.get("tag_no") or "").strip().upper()

        data = {
            "responsible": f.get("responsible"),
            "make_brand": f.get("make_brand"),
            "cyl_no": f.get("cyl_no"),
            "capacity": f.get("capacity"),
            "tag_no": tag,  # <- normalize edilmiş değer
            "location": f.get("location"),
            "sub_location": f.get("sub_location"),
            "hyd_ins_date": f.get("hyd_ins_date"),
            "hyd_due_date": f.get("hyd_due_date"),
            "refilling_filled_date": f.get("refilling_filled_date"),
            "refilling_due_date": f.get("refilling_due_date"),
            "monthly_ins_date": f.get("monthly_ins_date"),
            "monthly_due_date": f.get("monthly_due_date"),
            "mask_status": f.get("mask_status"),
            "cyl_pressure_bar": f.get("cyl_pressure_bar"),
            "straps_status": f.get("straps_status"),
            "bag_status": f.get("bag_status"),
            "overall_condition": f.get("overall_condition"),
            "inspected_by": f.get("inspected_by"),
            "remarks": f.get("remarks"),
            "corrective_action": f.get("corrective_action"),
        }

        with get_db() as con:
            con.execute("""
                INSERT INTO eebas (
                    responsible, make_brand, cyl_no, capacity, tag_no, location, sub_location,
                    hyd_ins_date, hyd_due_date, refilling_filled_date, refilling_due_date,
                    monthly_ins_date, monthly_due_date, mask_status, cyl_pressure_bar,
                    straps_status, bag_status, overall_condition, inspected_by, remarks, corrective_action
                ) VALUES (
                    :responsible, :make_brand, :cyl_no, :capacity, :tag_no, :location, :sub_location,
                    :hyd_ins_date, :hyd_due_date, :refilling_filled_date, :refilling_due_date,
                    :monthly_ins_date, :monthly_due_date, :mask_status, :cyl_pressure_bar,
                    :straps_status, :bag_status, :overall_condition, :inspected_by, :remarks, :corrective_action
                )
                ON CONFLICT(tag_no) DO UPDATE SET
                    responsible=excluded.responsible,
                    make_brand=excluded.make_brand,
                    cyl_no=excluded.cyl_no,
                    capacity=excluded.capacity,
                    location=excluded.location,
                    sub_location=excluded.sub_location,
                    hyd_ins_date=excluded.hyd_ins_date,
                    hyd_due_date=excluded.hyd_due_date,
                    refilling_filled_date=excluded.refilling_filled_date,
                    refilling_due_date=excluded.refilling_due_date,
                    monthly_ins_date=excluded.monthly_ins_date,
                    monthly_due_date=excluded.monthly_due_date,
                    mask_status=excluded.mask_status,
                    cyl_pressure_bar=excluded.cyl_pressure_bar,
                    straps_status=excluded.straps_status,
                    bag_status=excluded.bag_status,
                    overall_condition=excluded.overall_condition,
                    inspected_by=excluded.inspected_by,
                    remarks=excluded.remarks,
                    corrective_action=excluded.corrective_action
            """, data)

        flash("EEBA kaydı kaydedildi (varsa güncellendi).", "success")
        return redirect(url_for("eeba_bp.list_eeba"))

    # GET: dropdown için şirketleri yükle
    with get_db() as con:
        companies = con.execute(
            "SELECT id, company_name FROM companies ORDER BY company_name"
        ).fetchall()
    return render_template("eeba/add_eeba.html", companies=companies)


# ---------- Upload EEBA (Excel) ----------
@eeba_bp.route("/upload", methods=["GET", "POST"])
def upload_eeba():
    if request.method == "GET":
        return render_template("eeba/upload_eeba.html")

    f = request.files.get("file")
    on_conflict = request.form.get("on_conflict", "update")  # "update" | "skip"

    if not f or f.filename == "":
        flash("No file selected.", "warning")
        return redirect(url_for("eeba_bp.upload_eeba"))

    ext = Path(f.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        flash("Invalid file type. Please upload .xlsx", "danger")
        return redirect(url_for("eeba_bp.upload_eeba"))

    # Boyut kontrol
    f.seek(0, os.SEEK_END)
    size_mb = f.tell() / (1024 * 1024)
    f.seek(0)
    if size_mb > UPLOAD_MAX_MB:
        flash(f"File too large ({size_mb:.1f} MB). Max {UPLOAD_MAX_MB} MB.", "danger")
        return redirect(url_for("eeba_bp.upload_eeba"))

    # Excel'i oku
    try:
        df = pd.read_excel(f)  # engine=openpyxl varsayılan genelde yeterli
    except Exception as e:
        flash(f"Failed to read Excel: {e}", "danger")
        return redirect(url_for("eeba_bp.upload_eeba"))

    # Excel -> DB kolon eşlemesi
    COLMAP = {
        "RESPONSIBLE": "responsible",
        "MAKE / BRAND": "make_brand",
        "CYL.NO.": "cyl_no",
        "CAPACITY": "capacity",
        "TAG NO.": "tag_no",
        "LOCATION": "location",
        "SUB LOCATION": "sub_location",
        "HYD TEST DATE - INS. DATE": "hyd_ins_date",
        "HYD TEST DATE - DUE DATE": "hyd_due_date",
        "REFILLING STATUS - FILLED DATE": "refilling_filled_date",
        "REFILLING STATUS - DUE DATE": "refilling_due_date",
        "MONTHLY INSPECTIONS - INS. DATE": "monthly_ins_date",
        "MONTHLY INSPECTIONS - DUE DATE": "monthly_due_date",
        "MASK": "mask_status",
        "CYLINDER PRESSURE IN BAR": "cyl_pressure_bar",
        "STRAPS": "straps_status",
        "BAG": "bag_status",
        "OVERALL CONDITION": "overall_condition",
        "INSPECTED BY": "inspected_by",
        "REMARKS": "remarks",
        "CORRECTIVE ACTION": "corrective_action",
    }

    # Başlıkları sadeleştir
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in COLMAP if c not in df.columns]
    if missing:
        flash("Missing columns: " + ", ".join(missing), "danger")
        return redirect(url_for("eeba_bp.upload_eeba"))

    # Yardımcılar
    def to_date_str(v):
        """Her türlü girdiyi güvenle YYYY-MM-DD stringine çevirir; olmazsa None döner."""
        if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and v.strip() == ""):
            return None
        try:
            if isinstance(v, (pd.Timestamp, datetime)):
                return v.strftime("%Y-%m-%d")
            dt = pd.to_datetime(v, dayfirst=True, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    def normalize_ok_fail(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        s = str(v).strip().upper()
        if s in {"OK", "PASS", "PASSED", "SATISFACTORY"}:
            return "OK"
        if s in {"FAIL", "FAILED", "UNSATISFACTORY", "NOT OK", "NOT_OK", "NOT-OK"}:
            return "FAIL"
        return str(v).strip()

    DATE_FIELDS = {
        "hyd_ins_date", "hyd_due_date",
        "refilling_filled_date", "refilling_due_date",
        "monthly_ins_date", "monthly_due_date",
    }

    records = []
    for _, row in df.iterrows():
        rec = {}
        for xls_col, db_col in COLMAP.items():
            val = row.get(xls_col, None)

            # Tarihler
            if db_col in DATE_FIELDS:
                val = to_date_str(val)

            # OK/FAIL normalizasyonu
            if db_col in {"mask_status", "straps_status", "bag_status"}:
                val = normalize_ok_fail(val)

            # Basınç numeric
            if db_col == "cyl_pressure_bar":
                if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and val.strip() == ""):
                    val = None
                else:
                    try:
                        val = float(val)
                    except Exception:
                        val = None

            # Genel trim
            if isinstance(val, str):
                val = val.strip()

            # Atama
            rec[db_col] = None if (isinstance(val, float) and pd.isna(val)) else val

        # TAG NO zorunlu + normalize (trim + UPPER)
        if not rec.get("tag_no"):
            continue
        rec["tag_no"] = str(rec["tag_no"]).strip().upper()

        records.append(rec)

    if not records:
        flash("No valid rows found.", "warning")
        return redirect(url_for("eeba_bp.upload_eeba"))

    # Toplu ekleme / güncelleme
    with get_db() as con:
        if on_conflict == "update":
            sql = """
            INSERT INTO eebas (
                responsible, make_brand, cyl_no, capacity, tag_no, location, sub_location,
                hyd_ins_date, hyd_due_date, refilling_filled_date, refilling_due_date,
                monthly_ins_date, monthly_due_date, mask_status, cyl_pressure_bar,
                straps_status, bag_status, overall_condition, inspected_by, remarks, corrective_action
            ) VALUES (
                :responsible, :make_brand, :cyl_no, :capacity, :tag_no, :location, :sub_location,
                :hyd_ins_date, :hyd_due_date, :refilling_filled_date, :refilling_due_date,
                :monthly_ins_date, :monthly_due_date, :mask_status, :cyl_pressure_bar,
                :straps_status, :bag_status, :overall_condition, :inspected_by, :remarks, :corrective_action
            )
            ON CONFLICT(tag_no) DO UPDATE SET
                responsible=excluded.responsible,
                make_brand=excluded.make_brand,
                cyl_no=excluded.cyl_no,
                capacity=excluded.capacity,
                location=excluded.location,
                sub_location=excluded.sub_location,
                hyd_ins_date=excluded.hyd_ins_date,
                hyd_due_date=excluded.hyd_due_date,
                refilling_filled_date=excluded.refilling_filled_date,
                refilling_due_date=excluded.refilling_due_date,
                monthly_ins_date=excluded.monthly_ins_date,
                monthly_due_date=excluded.monthly_due_date,
                mask_status=excluded.mask_status,
                cyl_pressure_bar=excluded.cyl_pressure_bar,
                straps_status=excluded.straps_status,
                bag_status=excluded.bag_status,
                overall_condition=excluded.overall_condition,
                inspected_by=excluded.inspected_by,
                remarks=excluded.remarks,
                corrective_action=excluded.corrective_action
            ;
            """
        else:
            # on_conflict == "skip"
            sql = """
            INSERT OR IGNORE INTO eebas (
                responsible, make_brand, cyl_no, capacity, tag_no, location, sub_location,
                hyd_ins_date, hyd_due_date, refilling_filled_date, refilling_due_date,
                monthly_ins_date, monthly_due_date, mask_status, cyl_pressure_bar,
                straps_status, bag_status, overall_condition, inspected_by, remarks, corrective_action
            ) VALUES (
                :responsible, :make_brand, :cyl_no, :capacity, :tag_no, :location, :sub_location,
                :hyd_ins_date, :hyd_due_date, :refilling_filled_date, :refilling_due_date,
                :monthly_ins_date, :monthly_due_date, :mask_status, :cyl_pressure_bar,
                :straps_status, :bag_status, :overall_condition, :inspected_by, :remarks, :corrective_action
            );
            """
        con.executemany(sql, records)
        con.commit()

    flash(f"Imported {len(records)} row(s) successfully.", "success")
    return redirect(url_for("eeba_bp.list_eeba"))

####

# ---------- List ----------
@eeba_bp.route("/list")
def list_eeba():
    with get_db() as con:
        rows = con.execute("SELECT * FROM eebas ORDER BY location, sub_location, tag_no").fetchall()
    return render_template("eeba/list_eeba.html", rows=rows)

# ---------- Manual Scan ----------
@eeba_bp.route("/scan", methods=["GET","POST"])
def manual_scan_eeba():
    if request.method == "POST":
        tag = request.form.get("tag_no", "").strip()
        return redirect(url_for("eeba_bp.eeba_detail_by_tag", tag_no=tag))
    return render_template("eeba/manual_scan_eeba.html")

# ---------- Detail ----------
@eeba_bp.route("/detail/<tag_no>", methods=["GET", "POST"])
def eeba_detail_by_tag(tag_no):
    if request.method == "POST":
        f = request.form
        with get_db() as con:
            con.execute("""
                UPDATE eebas SET
                    responsible = ?,
                    make_brand = ?,
                    cyl_no = ?,
                    capacity = ?,
                    location = ?,
                    sub_location = ?,
                    hyd_ins_date = ?,
                    hyd_due_date = ?,
                    refilling_filled_date = ?,
                    refilling_due_date = ?,
                    monthly_ins_date = ?,
                    monthly_due_date = ?,
                    mask_status = ?,
                    cyl_pressure_bar = ?,
                    straps_status = ?,
                    bag_status = ?,
                    overall_condition = ?,
                    inspected_by = ?,
                    remarks = ?,
                    corrective_action = ?
                WHERE tag_no = ?;
            """, (
                f.get("responsible"), f.get("make_brand"), f.get("cyl_no"), f.get("capacity"),
                f.get("location"), f.get("sub_location"),
                f.get("hyd_ins_date"), f.get("hyd_due_date"),
                f.get("refilling_filled_date"), f.get("refilling_due_date"),
                f.get("monthly_ins_date"), f.get("monthly_due_date"),
                f.get("mask_status"), f.get("cyl_pressure_bar"),
                f.get("straps_status"), f.get("bag_status"), f.get("overall_condition"),
                f.get("inspected_by"), f.get("remarks"), f.get("corrective_action"),
                tag_no
            ))
        flash("EEBA kaydı güncellendi.", "success")
        return redirect(url_for("eeba_bp.eeba_detail_by_tag", tag_no=tag_no))

    with get_db() as con:
        row = con.execute("SELECT * FROM eebas WHERE tag_no = ?", (tag_no,)).fetchone()
    if not row:
        flash("Kayıt bulunamadı.", "warning")
        return redirect(url_for("eeba_bp.list_eeba"))
    return render_template("eeba/detail_eeba.html", row=row)

# ---------- Download Template ----------
@eeba_bp.route("/template.xlsx")
def download_eeba_template():
    cols = [
        "RESPONSIBLE","MAKE / BRAND","CYL.NO.","CAPACITY","TAG NO.","LOCATION","SUB LOCATION",
        "HYD TEST DATE - INS. DATE","HYD TEST DATE - DUE DATE",
        "REFILLING STATUS - FILLED DATE","REFILLING STATUS - DUE DATE",
        "MONTHLY INSPECTIONS - INS. DATE","MONTHLY INSPECTIONS - DUE DATE",
        "MASK","CYLINDER PRESSURE IN BAR","STRAPS","BAG","OVERALL CONDITION",
        "INSPECTED BY","REMARKS","CORRECTIVE ACTION"
    ]
    df = pd.DataFrame(columns=cols)
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="EEBA")
    bio.seek(0)
    return send_file(
        bio,
        as_attachment=True,
        download_name="eeba_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

#### EDIT

@eeba_bp.route("/edit/<int:id>", methods=["GET"], endpoint="edit_eeba_redirect")
def eeba_edit_redirect(id):
    with get_db() as con:
        row = con.execute("SELECT tag_no FROM eebas WHERE id = ?", (id,)).fetchone()
    if not row:
        flash("Kayıt bulunamadı.", "warning")
        return redirect(url_for("eeba_bp.list_eeba"))
    return redirect(url_for("eeba_bp.eeba_detail_by_tag", tag_no=row["tag_no"]))









###
### Sil Delete butonu
@eeba_bp.route("/delete/<int:id>", methods=["POST"])
def delete_eeba(id):
    with get_db() as con:
        con.execute("DELETE FROM eebas WHERE id = ?", (id,))
        con.commit()
    flash("EEBA kaydı silindi.", "success")
    return redirect(url_for("eeba_bp.list_eeba"))
###






