import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
from dotenv import load_dotenv
from sheets_service import SheetsDB, TAB_SCHEMAS, ALL_MODULES, ALL_ROLES

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "rri-mamuju-digital-board-secret-2026")

db = SheetsDB()

STATION_INFO = {
    "name": "RRI Mamuju.",
    "subtitle": "Your station, synced",
    "address": "Jl. R.E. Martadinata, Kec. Simboro dan Kepulauan, Kab. Mamuju, Sulawesi Barat",
    "phone": "+62 822-9609-0996",
    "email": "lpprrimamuju@gmail.com",
    "streams": {
        "pro1": {
            "name": "RRI Pro 1 Mamuju",
            "freq": "96.0 FM",
            "url": "https://stream-node0.rri.co.id/streaming/20/9020/rrimamujupro1",
            "share": "https://play.rri.co.id/sharing/radio/010461"
        }
    },
    "portals": [
        {"label": "rri.co.id/mamuju", "url": "https://rri.co.id/mamuju"},
        {"label": "PPID Mamuju", "url": "https://mamuju.ppid.rri.go.id/"},
        {"label": "RRI Digital", "url": "https://play.rri.co.id/sharing/radio/010461"},
        {"label": "YouTube", "url": "https://www.youtube.com/@LPPRRIMamuju"},
        {"label": "@rri_mamuju", "url": "https://www.instagram.com/rri_mamuju/"},
        {"label": "@pro2_mamuju", "url": "https://www.instagram.com/pro2_mamuju/"},
        {"label": "Linktree", "url": "https://linktr.ee/rri_mamuju"}
    ],
    "office_systems": [
        {"label": "PPID", "url": "https://mamuju.ppid.rri.go.id/"},
        {"label": "ASN-DIGITAL", "url": "https://asndigital.bkn.go.id/"},
        {"label": "SRIKANDI", "url": "https://srikandi.arsip.go.id/"},
        {"label": "SAKTI", "url": "https://sakti.kemenkeu.go.id/"},
        {"label": "RRI Digital", "url": "https://dashboard-rri.svara.id/"}
    ]
}

TARGET_PERMISSION_MAP = {
    "Timeline": ("dialog", "full"),
    "Agenda_Setting": ("dialog", "full"),
    "Planner": ("konten", "full"),
    "Siaran": ("jadwal_siaran", "full"),
    "Program_Siaran": ("program_siaran", "full"),
    "Jadwal_TMB": ("jadwal_tmb", "full"),
    "Arsip": ("info_board", "full"),
    "Info_Board": ("info_board", "full"),
    "Arsip_SDM": ("arsip_sdm", "full"),
    "DB_Pegawai": ("data_pegawai", "full"),
    "DB_Aset": ("master_barang", "full"),
    "DB_Ruangan": ("master_ruangan", "full"),
    "DB_Stok_Master": ("master_persediaan", "full"),
    "DB_Stok_Masuk": ("persediaan_masuk", "full"),
    "DB_Stok_Keluar": ("persediaan_keluar", "full"),
}

LEVEL_RANK = {"none": 0, "view": 1, "update": 2, "full": 3}


def _has_perm(user, module_key, min_level="view"):
    if not user:
        return False
    roles = user.get("roles") or []
    if any(r.lower() == "admin" for r in roles):
        return True
    perms = user.get("permissions") or {}
    cur = perms.get(module_key, "none")
    return LEVEL_RANK.get(cur, 0) >= LEVEL_RANK.get(min_level, 1)


@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", station=STATION_INFO, user=user)


@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("index"))
    user["permissions"] = db.compute_effective_permissions(user.get("roles", []))
    session["user"] = user
    return render_template(
        "dashboard.html",
        station=STATION_INFO,
        user=user,
        all_roles=ALL_ROLES,
        all_modules=ALL_MODULES,
    )


@app.route("/favicon.svg")
def favicon():
    static_path = os.path.join(app.root_path, "static", "favicon.svg")
    if os.path.exists(static_path):
        return send_from_directory(os.path.join(app.root_path, "static"), "favicon.svg", mimetype="image/svg+xml")
    return send_from_directory(app.template_folder, "favicon.svg", mimetype="image/svg+xml")


@app.route("/api/board")
def api_board():
    user = session.get("user")
    if user:
        user["permissions"] = db.compute_effective_permissions(user.get("roles", []))
        session["user"] = user

    can_see_stock = bool(user and (
        _has_perm(user, "master_persediaan", "view") or
        _has_perm(user, "persediaan_masuk", "view") or
        _has_perm(user, "persediaan_keluar", "view")
    ))
    stock_bundle = db.get_stock_bundle() if can_see_stock else {"master": [], "in_list": [], "out_list": []}
    existing_tabs = db.get_existing_tab_names() if user else []
    missing_tabs = [t for t in TAB_SCHEMAS.keys() if t.lower() not in {x.lower() for x in existing_tabs}] if db.connected else list(TAB_SCHEMAS.keys())

    is_admin = bool(user and any(r.lower() == "admin" for r in user.get("roles", [])))

    payload = {
        "connected": db.connected,
        "status_msg": "Live Google Sheets" if db.connected else (db.last_error or "Mode Demo"),
        "server_time": datetime.now().strftime("%d %b %Y • %H:%M WITA"),
        "authenticated": bool(user),
        "user": user,
        "all_roles": ALL_ROLES,
        "all_modules": ALL_MODULES,
        "role_matrix": db.get_role_matrix() if is_admin else {},
        "existing_tabs": existing_tabs,
        "missing_tabs": missing_tabs,
        "timeline": db.get_timeline(),
        "dialogs": db.get_agenda_setting(),
        "archive": db.get_tab_records("Arsip"),
        "info_board": db.get_tab_records("Info_Board", include_row_num=True) if user else [],
        "planner": db.get_tab_records("Planner", include_row_num=True) if _has_perm(user, "konten", "view") else [],
        "siaran": db.get_tab_records("Siaran", include_row_num=True) if _has_perm(user, "jadwal_siaran", "view") else [],
        "program_siaran": db.get_tab_records("Program_Siaran", include_row_num=True),
        "jadwal_tmb": db.get_tab_records("Jadwal_TMB", include_row_num=True) if _has_perm(user, "jadwal_tmb", "view") else [],
        "arsip_sdm": db.get_tab_records("Arsip_SDM", include_row_num=True) if _has_perm(user, "arsip_sdm", "view") else [],
        "employees": db.get_employees() if (_has_perm(user, "data_pegawai", "view") or _has_perm(user, "master_ruangan", "view") or is_admin) else [],
        "users_list": db.get_users_list() if is_admin else [],
        "assets": db.get_assets() if _has_perm(user, "master_barang", "view") else [],
        "rooms": db.get_rooms() if (_has_perm(user, "master_ruangan", "view") or _has_perm(user, "master_barang", "view")) else [],
        "stock_master": stock_bundle["master"],
        "stock_in": stock_bundle["in_list"],
        "stock_out": stock_bundle["out_list"],
    }
    return jsonify(payload)


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    employee_id = str(data.get("employee_id", "")).strip()
    password = str(data.get("password", "")).strip()

    user_info = db.authenticate_employee(employee_id, password)
    if user_info:
        session["user"] = user_info
        return jsonify({"ok": True, "user": user_info, "redirect": "/dashboard"})

    return jsonify({
        "ok": False,
        "message": "NIP / NIPPPK atau Password salah."
    }), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify({"ok": True})


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    db.clear_cache()
    return jsonify({"ok": True, "message": "Cache diperbarui."})


@app.route("/api/init-data", methods=["POST"])
def api_init_data():
    user = session.get("user")
    if not user or not any(r.lower() == "admin" for r in user.get("roles", [])):
        return jsonify({"ok": False, "message": "Hanya Admin yang dapat menjalankan Initial Data."}), 403

    data = request.get_json(silent=True) or {}
    include_samples = bool(data.get("include_samples", True))
    ok, msg = db.init_database_tabs(include_sample_rows=include_samples)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/admin/users", methods=["POST"])
def api_admin_save_user():
    user = session.get("user")
    if not user or not any(r.lower() == "admin" for r in user.get("roles", [])):
        return jsonify({"ok": False, "message": "Hanya Admin yang dapat mengelola akun user."}), 403

    data = request.get_json(silent=True) or {}
    nip = data.get("nip", "")
    password = data.get("password", "")
    roles = data.get("roles", [])
    ok, msg = db.save_user_account(nip, password, roles)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/admin/role-modules", methods=["POST"])
def api_admin_update_role_module():
    user = session.get("user")
    if not user or not any(r.lower() == "admin" for r in user.get("roles", [])):
        return jsonify({"ok": False, "message": "Hanya Admin yang dapat mengatur hak akses modul."}), 403

    data = request.get_json(silent=True) or {}
    role_name = data.get("role", "")
    module_key = data.get("module_key", "")
    level = data.get("level", "none")
    ok, msg = db.update_role_module_permission(role_name, module_key, level)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/employees/update", methods=["POST"])
def api_update_employee():
    user = session.get("user")
    if not _has_perm(user, "data_pegawai", "update"):
        return jsonify({"ok": False, "message": "Anda tidak memiliki izin edit pada modul Data Pegawai."}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num:
        return jsonify({"ok": False, "message": "Baris pegawai tidak ditemukan."}), 400

    ok, msg = db.update_employee_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/dialog/update", methods=["POST"])
def api_update_dialog():
    user = session.get("user")
    if not _has_perm(user, "dialog", "update"):
        return jsonify({"ok": False, "message": "Anda tidak memiliki izin update pada modul Dialog."}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num:
        return jsonify({"ok": False, "message": "Baris Dialog tidak ditemukan."}), 400

    ok, msg = db.update_dialog_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/add/<target_key>", methods=["POST"])
def api_add_record(target_key):
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Silakan login terlebih dahulu."}), 401

    if target_key not in TARGET_PERMISSION_MAP:
        return jsonify({"ok": False, "message": "Target modul tidak valid."}), 400

    mod_key, req_lvl = TARGET_PERMISSION_MAP[target_key]
    if not _has_perm(user, mod_key, req_lvl):
        return jsonify({"ok": False, "message": f"Role Anda tidak memiliki izin menambah data pada '{mod_key}'."}), 403

    row_data = request.get_json(silent=True) or {}
    ok, msg = db.append_record(target_key, row_data)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/delete/<target_key>", methods=["POST"])
def api_delete_record(target_key):
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Silakan login terlebih dahulu."}), 401

    if target_key not in TARGET_PERMISSION_MAP:
        return jsonify({"ok": False, "message": "Target modul tidak valid."}), 400

    mod_key, req_lvl = TARGET_PERMISSION_MAP[target_key]
    if not _has_perm(user, mod_key, req_lvl):
        return jsonify({"ok": False, "message": f"Role Anda tidak memiliki izin menghapus data pada '{mod_key}'."}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    if not row_num:
        return jsonify({"ok": False, "message": "Nomor baris tidak valid."}), 400

    ok, msg = db.delete_record(target_key, row_num)
    return jsonify({"ok": ok, "message": msg})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
