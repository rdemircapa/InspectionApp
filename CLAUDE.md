# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# Development (from project root — C:\InspectionApp)
flask run --debug

# Or with gunicorn (matches Docker target)
gunicorn --bind 0.0.0.0:8000 --workers 2 app:app
```

There are no automated tests. Manual browser testing is the only verification path.

## Docker / deploy

```bash
docker build -t inspectionapp .
docker run -p 8000:8000 \
  -e SECRET_KEY=... \
  -e DATABASE_PATH=/data/database.db \
  -e OUTPUT_FOLDER=/data/output \
  -v /data:/data \
  inspectionapp
```

The app is targeted at Easypanel. The Dockerfile is in the repo root; source is also at the repo root (no `mysite/` subdirectory).

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | `your_super_secret_key_12345` | Must be set in production; read via `os.getenv` in `app.py:7` |
| `DATABASE_PATH` | `<project_root>/database.db` | Absolute path to the SQLite file |
| `OUTPUT_FOLDER` | `<project_root>/output` | Where generated PDFs are written |

A `.env` file at the project root is used for local development.

## Architecture

**Partially-modular Flask monolith.** `app.py` is ~3900 lines and owns auth, products, SCBA, and fire extinguisher logic. Four equipment types are split into Blueprints, all registered in `app.py`:

| Blueprint | Module | Status |
|---|---|---|
| `eeba_bp` | `eeba/routes.py` | Active, has Excel bulk upload |
| `area_gas_monitor_bp` | `area_gas_monitor/routes.py` | Active, has GPS map views |
| `personal_gas_monitor_bp` | `personal_gas_monitor/` | Active |
| `new_module_bp` | `new_module/routes.py` | Skeleton only — no real functionality |

`gps_module/` is defined but **never registered** (dead code). `blueprints/fire_extinguisher.py` is empty — fire extinguisher logic lives in `app.py`.

The same CRUD + inspection + PDF pattern is repeated for each equipment type with no shared abstraction. There are 94 routes total.

## Tech stack

- **PDF/QR generation:** `reportlab` + `qrcode[pil]` — produces paginated card PDFs (`output/cards_page_N.pdf`) and in-memory summary reports
- **Excel import:** `pandas` — used in EEBA and SCBA bulk upload routes
- **Auth:** `bcrypt` password hashing + Flask `session`
- **Date parsing:** `python-dateutil`

`utils.py` contains a single helper: `normalize_result(value)` — normalizes inspection outcomes to `'Pass'`, `'Fail'`, or `'N/A'`.

## Key data model facts

- **Single SQLite file** (`database.db`), raw `sqlite3` — no ORM, no migration tool.
- **Two user tables** that serve different purposes:
  - `auth_users` — the real login table (id, username, full_name, role, bcrypt-hashed password)
  - `users` (badge_number, full_name) — used only for product assignment badge lookups
- **SCBA has two parallel models** that are both active:
  - `scba_units` (953 rows) — primary, used by most routes
  - `cylinders` + `regulators` + `scba_assemblies` — added later; `sync_scba_units_to_cylinders_and_regulators.py` syncs between them. These were an incomplete migration attempt.
- `eebas` is the best-designed table (trigger-maintained `updated_at`, indexes, CHECK constraints) — use it as a schema reference when adding new equipment types.
- `area_gas_monitors` has duplicate GPS columns: `latitude`/`longitude` AND `gps_latitude`/`gps_longitude`.
- `config.py` defines a `Config` class that is **never imported** anywhere.
- The generic `products`/`inspections`/`assignments` tables have almost no data (1–2 rows each) — they were an abandoned general-purpose equipment system.

## Auth & roles

- Session-based login (`/login`), `bcrypt` password hashing.
- Roles: `admin`, `inspector`, `viewer` — enforced by `@login_required` and `@role_required(...)` decorators from `auth_utils.py`.
- `requires_roles(...)` defined in `app.py` is a **duplicate** of `role_required` from `auth_utils.py` — prefer the one from `auth_utils.py`.

## Key workflows

1. **QR/tag inspection:** Each equipment has a unique tag (`cards` table, 208 rows). Field workers scan QR or enter tag manually → inspection form opens → result saved.
2. **PDF/label generation:** `reportlab` produces paginated QR card sheets written to `OUTPUT_FOLDER`, plus in-memory summary/assignment PDFs served directly.
3. **Excel bulk upload:** EEBA and SCBA support `.xlsx` import via `pandas`. At minimum the `eeba_bp` and the SCBA upload route (`/upload_scba`) implement this.
4. **BigQuery export:** `upload_to_bigquery.py` exports `fire_extinguishers` to BigQuery — manual only, requires the service account key `deft-citizen-466607-q7-a0a53ceeef2a.json`.

## Mobile/desktop split

Routes check `request.user_agent` for "android/iphone/ipad/mobile" (`app.py` around line 3470) and render separate templates (e.g., `inspect_fire_extinguisher.html` vs `inspect_fire_extinguisher_mobile.html`). Changing an inspection form requires editing both templates.

## Utility scripts (not part of the web app)

Run manually, not imported by `app.py`:
- `scba_tablolari.py` — created the cylinder/regulator/assembly schema
- `scba_tag_number.py` — one-time tag assignment
- `sync_scba_units_to_cylinders_and_regulators.py` — syncs the two SCBA models
- `init_eebas_db.py` — created the eebas table
- `tagcheck.py` — tag validation utility
- `upload_to_bigquery.py` — manual one-way export of `fire_extinguishers` to BigQuery

## Further reading

`ARCHITECTURE.md` (Turkish) contains a detailed analysis of the current architecture, full schema dump with live row counts, known technical debt list, and v2 design questions.
