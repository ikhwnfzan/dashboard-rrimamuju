import os
import base64
import copy
import json
from datetime import datetime, timedelta, timezone
from flask import Flask, abort, render_template, request, jsonify, session, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sheets_service import (
    APP_CONFIG_DEFAULTS,
    SheetsDB,
    DB_SCHEMAS,
    ALL_MODULES,
    ALL_ROLES,
)
from media_service import MediaFeedService

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY belum diatur di environment.")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

db = SheetsDB()
media_feed = MediaFeedService()

APP_CONFIG_CHOICES = {
    "timezone": ("WIB", "WITA", "WIT", "UTC"),
    "language": ("id", "en"),
    "default_theme": ("light", "dark"),
    "active_year": tuple(
        str(year)
        for year in range(
            int(APP_CONFIG_DEFAULTS["active_year"]),
            int(APP_CONFIG_DEFAULTS["active_year"]) - 5,
            -1,
        )
    ),
}
APP_TIMEZONES = {
    "WIB": timezone(timedelta(hours=7), "WIB"),
    "WITA": timezone(timedelta(hours=8), "WITA"),
    "WIT": timezone(timedelta(hours=9), "WIT"),
    "UTC": timezone.utc,
}


def _is_admin(user):
    return bool(user and any(r.lower() == "admin" for r in user.get("roles", [])))


def _get_app_config():
    config = dict(APP_CONFIG_DEFAULTS)
    config["station_info"] = copy.deepcopy(STATION_INFO)
    for setting in db.get_app_settings():
        key = str(setting.get("key", "")).strip()
        if key in config:
            value = str(setting.get("value", "")).strip()
            if key == "station_info":
                if not value:
                    continue
                try:
                    station_info = json.loads(value)
                except json.JSONDecodeError:
                    app.logger.warning("Ignoring invalid CFG_App station_info JSON.")
                    continue
                if _is_valid_station_info(station_info):
                    config[key] = station_info
                else:
                    app.logger.warning("Ignoring invalid CFG_App station_info structure.")
            else:
                config[key] = value

    for key, options in APP_CONFIG_CHOICES.items():
        if config[key] not in options:
            app.logger.warning("Ignoring invalid CFG_App value for %s: %r", key, config[key])
            config[key] = APP_CONFIG_DEFAULTS[key]
    return config

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
            "url": "https://stream-node0.rri.co.id/streaming/20/9020/rrimamujupro1.mp3",
            "share": "https://play.rri.co.id/sharing/radio/010461"
        },
        "pro2": {
            "name": "RRI Pro 2 Mamuju",
            "freq": "89.3 FM",
            "url": "https://stream-node0.rri.co.id/streaming/20/9020/rrimamujupro2.mp3",
            "share": "https://play.rri.co.id/sharing/radio/015293"
        }
    },
    "links": [
        {"label": "PPID", "url": "https://mamuju.ppid.rri.go.id/"},
        {"label": "ASN-DIGITAL", "url": "https://asndigital.bkn.go.id/"},
        {"label": "SRIKANDI", "url": "https://srikandi.arsip.go.id/"},
        {"label": "SAKTI", "url": "https://sakti.kemenkeu.go.id/"},
        {"label": "RRI Digital", "url": "https://dashboard-rri.svara.id/"}
    ]
}

def _get_station_info():
    return _get_app_config()["station_info"]


def _is_valid_station_info(value):
    if not isinstance(value, dict) or set(value) != set(STATION_INFO):
        return False
    for key in ("name", "subtitle", "address", "phone", "email"):
        if not isinstance(value.get(key), str):
            return False

    streams = value.get("streams")
    if not isinstance(streams, dict) or set(streams) != set(STATION_INFO["streams"]):
        return False
    for stream_key, default_stream in STATION_INFO["streams"].items():
        stream = streams.get(stream_key)
        if not isinstance(stream, dict) or set(stream) != set(default_stream):
            return False
        if any(not isinstance(stream.get(field), str) for field in default_stream):
            return False

    links = value.get("links")
    if not isinstance(links, list):
        return False
    return all(
        isinstance(link, dict)
        and set(link) == {"label", "url"}
        and isinstance(link.get("label"), str)
        and isinstance(link.get("url"), str)
        for link in links
    )

TARGET_PERMISSION_MAP = {
    "DB_Timeline": ("dialog", "full"),
    "DB_Dialog": ("dialog", "full"),
    "DB_Flyer": ("dialog", "full"),
    "DB_Produksi_Paket": ("produksi_paket", "full"),
    "DB_Konten": ("konten", "full"),
    "DB_Socmed_Analytics": ("socmed_analytics", "full"),
    "DB_Jadwal_Operasional": ("jadwal_siaran", "full"),
    "DB_Program": ("program_siaran", "full"),
    "DB_TMB_Working_Progress": ("tmb_working_progresss", "full"),
    "DB_Info_Board": ("info_board", "full"),
    "DB_Arsip_Program": ("arsip_program", "full"),
    "DB_SDM_Arsip": ("arsip_sdm", "full"),
    "DB_Pegawai": ("data_pegawai", "full"),
    "DB_Aset": ("master_barang", "full"),
    "DB_Ruangan": ("master_ruangan", "full"),
    "DB_BAST": ("bast_otomatis", "full"),
    "DB_Pemeliharaan_Header": ("pemeliharaan_aset", "full"),
    "DB_Pemeliharaan_Detail": ("pemeliharaan_aset", "full"),
    "DB_BMN_Arsip": ("bmn_arsip", "full"),
    "DB_BMN_Dokumen": ("aset_tutup_buku", "full"),
    "DB_Stok_Master": ("master_persediaan", "full"),
    "DB_Stok_Detail": ("master_persediaan", "full"),
}

# Data payload groups loaded for an active module. The active module is always
# included; dependencies are modules or supporting datasets needed by its UI.
MODULE_DATA_DEPENDENCIES = {
    "overview": {"timeline", "info_board"},
    "user_profile": {"employees"},
    "info_board": {"info_board"},
    "data_pegawai": {"employees"},
    "arsip_sdm": {"arsip_sdm"},
    "dialog": {"dialogs", "timeline"},
    "jadwal_siaran": {"siaran"},
    "produksi_paket": {"produksi_paket"},
    "program_siaran": {"program_siaran"},
    "arsip_program": {"arsip_program"},
    "konten": {"content_planner"},
    "bestcut_monitoring": {"dialogs"},
    "socmed_analytics": {"socmed_analytics"},
    "jadwal_tmb": {"jadwal_tmb"},
    "tmb_working_progresss": {"tmb_working_progresss"},
    "master_barang": {"assets", "rooms", "employees"},
    "master_ruangan": {"rooms", "employees", "assets"},
    "bast_otomatis": {"rooms", "assets", "employees"},
    "pemeliharaan_aset": {"pemeliharaan_header", "pemeliharaan_detail", "assets"},
    "bmn_arsip": {"bmn_dokumen"},
    "aset_tutup_buku": {"bmn_dokumen"},
    "aset_calbmn": {"bmn_dokumen"},
    "aset_wasdal": {"bmn_dokumen"},
    "aset_rkbmn": {"bmn_dokumen"},
    "aset_manajemen_risiko": {"bmn_dokumen"},
    "aset_sisporja": {"bmn_dokumen"},
    "master_persediaan": {"stock"},
    "persediaan_tutup_buku": {"bmn_dokumen", "stock"},
    "persediaan_pipk": {"bmn_dokumen", "stock"},
    "manage_users": {"users_list", "all_roles"},
    "manage_modules": {"role_matrix", "all_roles", "all_modules"},
    "app_settings": {"app_config"},
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


def _get_module_payload(user, module_key):
    """Fetch only data required by the active module and its UI dependencies."""
    if not user:
        return {}

    is_admin = _is_admin(user)
    if module_key != "overview" and module_key != "user_profile" and not _has_perm(user, module_key, "view"):
        return {"active_module": module_key, "module_access": "denied"}

    dependencies = MODULE_DATA_DEPENDENCIES.get(module_key, set())
    payload = {"active_module": module_key}

    def can_fetch(module):
        return is_admin or _has_perm(user, module, "view")

    if "timeline" in dependencies:
        payload["timeline"] = db.get_timeline() if can_fetch("dialog") or module_key == "overview" else []
    if "dialogs" in dependencies:
        payload["dialogs"] = db.get_agenda_setting() if can_fetch("dialog") or module_key == "bestcut_monitoring" else []
    if "info_board" in dependencies:
        payload["info_board"] = db.get_tab_records(["DB_Info_Board"], include_row_num=True)
    if "produksi_paket" in dependencies:
        payload["produksi_paket"] = db.get_tmb_working_progress()
    if "content_planner" in dependencies:
        payload["content_planner"] = db.get_tab_records(["DB_Konten"], include_row_num=True)
    if "socmed_analytics" in dependencies:
        payload["socmed_analytics"] = db.get_tab_records(["DB_Socmed_Analytics"], include_row_num=True)
    if "siaran" in dependencies:
        payload["siaran"] = db.get_jadwal_operasional("siaran")
    if "program_siaran" in dependencies:
        payload["program_siaran"] = db.get_tab_records(["DB_Program"], include_row_num=True)
    if "arsip_program" in dependencies:
        payload["arsip_program"] = db.get_arsip_program()
    if "jadwal_tmb" in dependencies:
        payload["jadwal_tmb"] = db.get_jadwal_operasional("tmb")
    if "tmb_working_progresss" in dependencies:
        payload["tmb_working_progresss"] = db.get_tmb_working_progress()
    if "arsip_sdm" in dependencies:
        payload["arsip_sdm"] = db.get_arsip_sdm()
    if "employees" in dependencies:
        if can_fetch("data_pegawai") or module_key in {"master_barang", "master_ruangan", "bast_otomatis", "user_profile"}:
            payload["employees"] = db.get_employees()
        else:
            payload["employees"] = []
    if "assets" in dependencies:
        payload["assets"] = db.get_assets() if is_admin or can_fetch("master_barang") or can_fetch("bast_otomatis") or can_fetch("pemeliharaan_aset") else []
    if "rooms" in dependencies:
        payload["rooms"] = db.get_rooms() if is_admin or can_fetch("master_ruangan") or can_fetch("bast_otomatis") or can_fetch("master_barang") else []
    if "pemeliharaan_header" in dependencies:
        payload["pemeliharaan_header"] = db.get_tab_records(["DB_Pemeliharaan_Header"], include_row_num=True)
    if "pemeliharaan_detail" in dependencies:
        payload["pemeliharaan_detail"] = db.get_tab_records(["DB_Pemeliharaan_Detail"], include_row_num=True)
    # if "bmn_arsip" in dependencies:
    #     payload["bmn_arsip"] = db.get_tab_records(["DB_BMN_Arsip"], include_row_num=True)
    if "bmn_dokumen" in dependencies:
        payload["bmn_dokumen"] = db.get_tab_records(["DB_BMN_Dokumen"], include_row_num=True)
    if "stock" in dependencies:
        stock_bundle = db.get_stock_bundle()
        payload["stock_master"] = stock_bundle["master"]
        payload["stock_details"] = stock_bundle["details"]
    if "users_list" in dependencies:
        payload["users_list"] = db.get_users_list() if is_admin else []
    if "all_roles" in dependencies:
        payload["all_roles"] = ALL_ROLES
    if "all_modules" in dependencies:
        payload["all_modules"] = ALL_MODULES
    if "role_matrix" in dependencies:
        payload["role_matrix"] = db.get_role_matrix() if is_admin else {}

    return payload


def _validate_timeline_data(data):
    activity = str(data.get("Kegiatan", "")).strip()
    start_date = str(data.get("Tanggal Mulai", "")).strip()
    end_date = str(data.get("Tanggal Selesai", "")).strip()
    if not activity:
        return "Kegiatan wajib diisi."
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return "Tanggal mulai tidak valid."
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return "Tanggal selesai tidak valid."
        if end < start:
            return "Tanggal selesai tidak boleh sebelum tanggal mulai."
    return None


@app.context_processor
def inject_now():
    return {"now": lambda: datetime.now(timezone.utc)}


@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", station=_get_station_info(), user=user)


@app.route("/dashboard")
@app.route("/dashboard/<module_key>")
def dashboard(module_key="overview"):
    user = session.get("user")
    if not user:
        return redirect(url_for("index"))
    user["permissions"] = db.compute_effective_permissions(user.get("roles", []))
    session["user"] = user

    known_modules = {module["key"] for module in ALL_MODULES}
    known_modules.update({"overview", "user_profile", "persediaan_form_pengajuan", "app_settings"})
    if module_key not in known_modules:
        abort(404)
    if module_key == "app_settings":
        if not _is_admin(user):
            abort(404)
    elif module_key not in {"overview", "user_profile"} and not _has_perm(user, module_key, "view"):
        abort(404)

    return render_template(
        "dashboard.html",
        station=_get_station_info(),
        user=user,
        all_roles=ALL_ROLES,
        all_modules=ALL_MODULES,
        app_config=_get_app_config(),
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", user=session.get("user")), 404


@app.route("/favicon.svg")
def favicon():
    static_path = os.path.join(app.root_path, "static", "favicon.svg")
    if os.path.exists(static_path):
        return send_from_directory(os.path.join(app.root_path, "static"), "favicon.svg", mimetype="image/svg+xml")
    return send_from_directory(app.template_folder, "favicon.svg", mimetype="image/svg+xml")


@app.route("/api/module/<module_key>")
def api_module(module_key):
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Restricted access!"}), 401
    if user:
        user["permissions"] = db.compute_effective_permissions(user.get("roles", []))
        session["user"] = user
    payload = _get_module_payload(user, module_key)
    if payload.get("module_access") == "denied":
        return jsonify({"ok": False, "message": "Restricted access!", "active_module": module_key}), 403
    payload["ok"] = True
    return jsonify(payload)


@app.route("/api/user")
def api_user():
    user = session.get("user")
    if user:
        user["permissions"] = db.compute_effective_permissions(user.get("roles", []))
        session["user"] = user

    app_config = _get_app_config()
    is_admin = _is_admin(user)
    existing_tabs = db.get_existing_tab_names() if user else []
    missing_tabs = [t for t in DB_SCHEMAS.keys() if t.lower() not in {x.lower() for x in existing_tabs}] if db.connected else list(DB_SCHEMAS.keys())

    return jsonify({
        "connected": db.connected,
        "status_msg": "Database Synced" if db.connected else (db.last_error or "Database tidak terhubung"),
        "server_time": datetime.now(timezone.utc).astimezone(APP_TIMEZONES[app_config["timezone"]]).strftime("%d %b %Y • %H:%M %Z"),
        "app_config": app_config,
        "authenticated": bool(user),
        "user": user,
        "all_roles": ALL_ROLES,
        "all_modules": ALL_MODULES,
        "role_matrix": db.get_role_matrix() if is_admin else {},
        "existing_tabs": existing_tabs,
        "missing_tabs": missing_tabs,
    })


@app.route("/api/public/landing")
def api_public_landing():
    app_config = _get_app_config()
    return jsonify({
        "connected": db.connected,
        "status_msg": "Database Synced" if db.connected else (db.last_error or "Database tidak terhubung"),
        "server_time": datetime.now(timezone.utc).astimezone(APP_TIMEZONES[app_config["timezone"]]).strftime("%d %b %Y • %H:%M %Z"),
        "app_config": app_config,
        "timeline": db.get_timeline(),
        "dialogs": db.get_agenda_setting(),
        "program_siaran": db.get_tab_records(["DB_Program"], include_row_num=True),
        "youtube_feed": media_feed.get_youtube_feed(),
        "drive_flyers": media_feed.get_drive_flyers(),
    })


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    employee_id = str(data.get("employee_id", "")).strip()
    password = str(data.get("password", "")).strip()

    if not db.connected:
        return jsonify({
            "ok": False,
            "message": f"Database belum terhubung ({db.last_error})."
        }), 503

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
    media_feed.clear_cache()
    return jsonify({"ok": True, "message": "Cache diperbarui."})


@app.route("/api/admin/users", methods=["POST"])
def api_admin_save_user():
    user = session.get("user")
    if not user or not any(r.lower() == "admin" for r in user.get("roles", [])):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    nip = data.get("nip", "")
    password = data.get("password", "")
    roles = data.get("roles", [])
    ok, msg = db.save_user_account(nip, password, roles)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/admin/settings", methods=["POST"])
def api_admin_save_settings():
    user = session.get("user")
    if not _is_admin(user):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "Invalid data format!"}), 400
    settings = data.get("settings")
    allowed_settings = set(APP_CONFIG_DEFAULTS) | set(APP_CONFIG_CHOICES)
    if (
        not isinstance(settings, dict)
        or set(settings) - allowed_settings
        or not set(APP_CONFIG_CHOICES).issubset(settings)
        or "station_info" not in settings
    ):
        return jsonify({"ok": False, "message": "Invalid data format!"}), 400
    settings_to_save = dict(settings)
    for key, value in settings.items():
        if key in APP_CONFIG_CHOICES and value not in APP_CONFIG_CHOICES[key]:
            return jsonify({"ok": False, "message": f"'{key}' data is invalid!"}), 400
        if key == "station_info":
            if not _is_valid_station_info(value):
                return jsonify({"ok": False, "message": "'station_info' data is invalid!"}), 400
            settings_to_save[key] = json.dumps(value, ensure_ascii=False)
        elif not isinstance(value, str):
            return jsonify({"ok": False, "message": f"'{key}' data is invalid!"}), 400

    ok, msg = db.save_app_settings(settings_to_save)
    if not ok:
        return jsonify({"ok": False, "message": msg})
    return jsonify({"ok": True, "message": msg, "app_config": _get_app_config()})


@app.route("/api/bast/records", methods=["GET"])
def api_bast_records():
    user = session.get("user")
    if not _has_perm(user, "bast_otomatis", "view"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403
    return jsonify({"ok": True, "records": db.get_bast_records()})


@app.route("/api/bast/generate", methods=["POST"])
def api_bast_generate():
    user = session.get("user")
    if not _has_perm(user, "bast_otomatis", "full"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    payload = request.get_json(silent=True) or {}
    required = ["nomor_bast", "tanggal", "nama", "nip", "pangkat", "jabatan", "nomor_barang", "nup", "barang", "nilai", "jumlah", "letak"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"ok": False, "message": "Data BAST belum lengkap."}), 400

    template_doc_id = os.getenv("BAST_TEMPLATE_DOC_ID", "").strip()
    ok, result = db.generate_bast_document(payload, template_doc_id=template_doc_id)
    return jsonify({"ok": ok, **result})


@app.route("/api/bast/update", methods=["POST"])
def api_bast_update():
    user = session.get("user")
    if not _has_perm(user, "bast_otomatis", "update"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num or not isinstance(updates, dict):
        return jsonify({"ok": False, "message": "Invalid row number or BAST data!"}), 400

    allowed_fields = {"Nomor BAST", "NIP", "Nomor Barang", "NUP", "Nilai", "Jumlah"}
    if not set(updates).issubset(allowed_fields):
        return jsonify({"ok": False, "message": "Kolom BAST tidak valid."}), 400

    updates = {key: str(value or "").strip() for key, value in updates.items()}
    ok, msg = db.update_bast_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/admin/role-modules", methods=["POST"])
def api_admin_update_role_module():
    user = session.get("user")
    if not user or not any(r.lower() == "admin" for r in user.get("roles", [])):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

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
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num:
        return jsonify({"ok": False, "message": "Invalid row number!"}), 400

    ok, msg = db.update_employee_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/dialog/update", methods=["POST"])
def api_update_dialog():
    user = session.get("user")
    if not _has_perm(user, "dialog", "update"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num:
        return jsonify({"ok": False, "message": "Invalid row number!"}), 400

    ok, msg = db.update_dialog_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/assets/update", methods=["POST"])
def api_update_asset():
    user = session.get("user")
    if not _has_perm(user, "master_barang", "update"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num or not isinstance(updates, dict):
        return jsonify({"ok": False, "message": "Invalid row number or asset data!"}), 400

    allowed_fields = {"Kode Ruang", "Tipe", "Nama Barang", "Merk Model", "Tahun", "NUP", "Kondisi", "Tindak Lanjut", "Keterangan"}
    if not set(updates).issubset(allowed_fields):
        return jsonify({"ok": False, "message": "Kode Barang tidak dapat diubah."}), 400

    updates = {key: str(value or "").strip() for key, value in updates.items()}
    ok, msg = db.update_asset_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/rooms/update", methods=["POST"])
def api_update_room():
    user = session.get("user")
    if not _has_perm(user, "master_ruangan", "update"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num or not isinstance(updates, dict):
        return jsonify({"ok": False, "message": "Invalid row number or room data!"}), 400

    allowed_fields = {"Nama Ruangan", "Lokasi", "NIP Penanggung Jawab"}
    if not set(updates).issubset(allowed_fields):
        return jsonify({"ok": False, "message": "Nomor Ruangan tidak dapat diubah."}), 400

    updates = {key: str(value or "").strip() for key, value in updates.items()}
    ok, msg = db.update_room_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/timeline/update", methods=["POST"])
def api_update_timeline():
    user = session.get("user")
    if not _has_perm(user, "dialog", "update"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "Invalid data format!"}), 400
    row_num = data.get("row_num")
    updates = data.get("updates")
    if not row_num or not isinstance(updates, dict):
        return jsonify({"ok": False, "message": "Invalid row number or timeline data!"}), 400

    allowed_fields = {"Kegiatan", "Tahapan", "Tanggal Mulai", "Tanggal Selesai", "Keterangan", "Tanggal"}
    if not updates or not set(updates).issubset(allowed_fields):
        return jsonify({"ok": False, "message": "Invalid timeline columns!"}), 400
    validation_error = _validate_timeline_data(updates)
    if validation_error:
        return jsonify({"ok": False, "message": validation_error}), 400

    updates = {key: str(value or "").strip() for key, value in updates.items()}
    updates["Tanggal"] = updates.get("Tanggal Mulai", "")
    ok, msg = db.update_timeline_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/stok-detail/update", methods=["POST"])
def api_update_stok_detail():
    user = session.get("user")
    if not _has_perm(user, "master_persediaan", "update"):
        return jsonify({"ok": False, "message": "Restricted access!"}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    updates = data.get("updates") or {}
    if not row_num:
        return jsonify({"ok": False, "message": "Invalid row number!"}), 400

    ok, msg = db.update_stok_detail_row(row_num, updates)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/upload/bmn", methods=["POST"])
def api_upload_bmn_document():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Restricted access!"}), 401

    module_by_submenu = {
        ("Aset", "Tutup Buku"): "aset_tutup_buku",
        ("Aset", "CALBMN"): "aset_calbmn",
        ("Aset", "WASDAL"): "aset_wasdal",
        ("Aset", "RKBMN"): "aset_rkbmn",
        ("Aset", "Manajemen Risiko"): "aset_manajemen_risiko",
        ("Aset", "SISPORJA"): "aset_sisporja",
        ("Aset", "Arsip"): "bmn_arsip",
        ("Persediaan", "Tutup Buku"): "persediaan_tutup_buku",
        ("Persediaan", "PIPK"): "persediaan_pipk",
    }
    group_name = request.form.get("Group", "").strip()
    sub_menu = request.form.get("Sub Menu", "").strip()
    output_name = request.form.get("Judul Dokumen", "").strip()
    module_key = module_by_submenu.get((group_name, sub_menu))
    if not module_key:
        return jsonify({"ok": False, "message": "Bagian dokumen BMN tidak valid."}), 400
    if not _has_perm(user, module_key, "full"):
        return jsonify({"ok": False, "message": "Anda tidak memiliki hak upload dokumen."}), 403

    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"ok": False, "message": "Pilih file yang akan diunggah."}), 400

    allowed_extensions = {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "jpg", "jpeg", "png", "zip",
    }
    original_name = secure_filename(os.path.basename(uploaded.filename).strip())
    if not original_name:
        return jsonify({"ok": False, "message": "Nama file tidak valid."}), 400
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in allowed_extensions:
        return jsonify({"ok": False, "message": "Format file tidak didukung."}), 400
    drive_file_name = output_name.replace("\\", "-").replace("/", "-").strip()
    if not drive_file_name:
        return jsonify({"ok": False, "message": "Nama dokumen tidak valid."}), 400
    if not drive_file_name.lower().endswith(f".{extension}"):
        drive_file_name = f"{drive_file_name}.{extension}"

    row_data = {
        "Group": group_name,
        "Sub Menu": sub_menu,
        "Periode": request.form.get("Periode", "").strip(),
        "Kategori Item": request.form.get("Kategori Item", "").strip(),
        "Judul Dokumen": drive_file_name,
        "Tanggal Buat": request.form.get("Tanggal Buat", "").strip(),
        "Keterangan": request.form.get("Keterangan", "").strip(),
    }
    if not row_data["Judul Dokumen"] or not row_data["Tanggal Buat"]:
        return jsonify({"ok": False, "message": "Judul dan tanggal dokumen wajib diisi."}), 400

    bridge_url = os.getenv("DRIVE_BRIDGE_URL", "").strip()
    root_folder_id = os.getenv("DRIVE_ROOT_FOLDER_ID", "").strip()
    bridge_secret = os.getenv("DRIVE_BRIDGE_SECRET", "").strip()
    if not bridge_url or not root_folder_id:
        return jsonify({
            "ok": False,
            "message": "Google Drive belum dikonfigurasi. Isi Folder ID Utama dan URL Apps Script di App Setting.",
        }), 503

    try:
        import requests
        file_bytes = uploaded.read()
        if not file_bytes:
            return jsonify({"ok": False, "message": "File yang dipilih kosong."}), 400
        bridge_response = requests.post(
            bridge_url,
            json={
                "secret": bridge_secret,
                "action": "upload_file",
                "root_folder_id": root_folder_id,
                "group_name": group_name,
                "subfolder_name": sub_menu,
                "drive_file_name": drive_file_name,
                "mime_type": uploaded.mimetype or "application/octet-stream",
                "file_base64": base64.b64encode(file_bytes).decode("ascii"),
            },
            timeout=120,
            allow_redirects=True,
        )
        drive_result = bridge_response.json()
    except Exception as exc:
        app.logger.exception("BMN file upload to Drive failed")
        return jsonify({"ok": False, "message": f"Gagal mengunggah file ke Google Drive: {exc}"}), 502

    if (
        not bridge_response.ok
        or not isinstance(drive_result, dict)
        or not drive_result.get("ok")
    ):
        return jsonify({
            "ok": False,
            "message": (
                drive_result.get("message")
                if isinstance(drive_result, dict)
                else None
            ) or "Google Drive gagal menyimpan file.",
        }), 502

    drive_file_id = str(drive_result.get("file_id", "")).strip()
    drive_file_url = str(drive_result.get("file_url", "")).strip()
    saved_file_name = str(drive_result.get("file_name", "")).strip()
    if not drive_file_id or not drive_file_url or saved_file_name != drive_file_name:
        return jsonify({
            "ok": False,
            "message": "Google Drive belum mengonfirmasi file tersimpan dengan nama yang diminta.",
        }), 502

    row_data["Link File"] = drive_file_url
    ok, message = db.append_record("DB_BMN_Dokumen", row_data)
    if not ok:
        app.logger.error("Uploaded BMN file %s but failed to save its record: %s", drive_file_id, message)
        return jsonify({
            "ok": False,
            "message": f"File sudah tersimpan di Google Drive, tetapi data dokumen gagal disimpan: {message}",
        }), 500
    return jsonify({
        "ok": True,
        "message": "Dokumen dan file berhasil disimpan ke Google Drive.",
        "url": row_data["Link File"],
        "filename": drive_file_name,
        "folder": drive_result.get("folder_path", ""),
    })


@app.route("/api/persediaan/pengajuan", methods=["POST"])
def api_submit_persediaan_pengajuan():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Restricted access!"}), 401
    if not _has_perm(user, "persediaan_form_pengajuan", "update"):
        return jsonify({"ok": False, "message": "Anda tidak memiliki izin mengirim Form Pengajuan."}), 403

    nama_pengaju = str(request.form.get("nama_pengaju", "")).strip()
    tim = str(request.form.get("tim", "")).strip()
    nama_kegiatan = str(request.form.get("nama_kegiatan", "")).strip()
    uploaded = request.files.get("dokumen")

    if not nama_pengaju or not tim:
        return jsonify({"ok": False, "message": "Nama Pengaju dan Tim wajib diisi."}), 400
    if not uploaded or not uploaded.filename:
        return jsonify({"ok": False, "message": "Dokumen Surat Pengajuan Barang wajib dilampirkan."}), 400

    original_name = secure_filename(os.path.basename(uploaded.filename).strip())
    if not original_name:
        return jsonify({"ok": False, "message": "Nama file tidak valid."}), 400
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in {"doc", "docx", "pdf"}:
        return jsonify({"ok": False, "message": "Format file harus .doc, .docx, atau .pdf."}), 400

    file_bytes = uploaded.read()
    if not file_bytes:
        return jsonify({"ok": False, "message": "File dokumen kosong."}), 400

    bridge_url = os.getenv("DRIVE_BRIDGE_URL", "").strip()
    root_folder_id = os.getenv("DRIVE_ROOT_FOLDER_ID", "").strip()
    bridge_secret = os.getenv("DRIVE_BRIDGE_SECRET", "").strip()
    if not bridge_url or not root_folder_id:
        return jsonify({
            "ok": False,
            "message": "Google Drive belum dikonfigurasi. Isi Folder ID Utama dan URL Apps Script di App Setting.",
        }), 503

    today_str = datetime.now().strftime("%Y-%m-%d")
    periode_str = datetime.now().strftime("%Y-%m")
    raw_title = f"Pengajuan_{tim}_{nama_pengaju}_{today_str}_{original_name}"
    drive_file_name = raw_title.replace("\\", "-").replace("/", "-").replace(" ", "_")

    try:
        import base64
        import requests
        bridge_response = requests.post(
            bridge_url,
            json={
                "secret": bridge_secret,
                "action": "upload_file",
                "root_folder_id": root_folder_id,
                "group_name": "Persediaan",
                "subfolder_name": "Form Pengajuan",
                "drive_file_name": drive_file_name,
                "mime_type": uploaded.mimetype or "application/octet-stream",
                "file_base64": base64.b64encode(file_bytes).decode("ascii"),
            },
            timeout=60,
            allow_redirects=True,
        )
        drive_result = bridge_response.json()
    except Exception as exc:
        app.logger.exception("Pengajuan Persediaan file upload to Drive failed")
        return jsonify({"ok": False, "message": f"Gagal mengunggah file ke Google Drive: {exc}"}), 502

    if (
        not bridge_response.ok
        or not isinstance(drive_result, dict)
        or not drive_result.get("ok")
    ):
        return jsonify({
            "ok": False,
            "message": (
                drive_result.get("message")
                if isinstance(drive_result, dict)
                else None
            ) or "Google Drive gagal menyimpan file.",
        }), 502

    drive_file_url = str(drive_result.get("file_url", "")).strip()
    if not drive_file_url:
        return jsonify({
            "ok": False,
            "message": "Google Drive tidak mengembalikan tautan file.",
        }), 502

    judul_dokumen = nama_kegiatan if nama_kegiatan else f"Pengajuan Persediaan — {tim} ({nama_pengaju})"
    ket_parts = [f"Pengaju: {nama_pengaju}", f"Tim: {tim}"]
    if nama_kegiatan:
        ket_parts.append(f"Kegiatan: {nama_kegiatan}")

    ok_db, msg_db = db.append_record("DB_BMN_Dokumen", {
        "Group": "Persediaan",
        "Sub Menu": "Form Pengajuan",
        "Periode": periode_str,
        "Kategori Item": tim,
        "Judul Dokumen": judul_dokumen,
        "Tanggal Buat": today_str,
        "Link File": drive_file_url,
        "Keterangan": " • ".join(ket_parts),
    })
    if not ok_db:
        return jsonify({
            "ok": False,
            "message": f"File sudah tersimpan di Google Drive, tetapi data pengajuan gagal dicatat: {msg_db}",
        }), 500

    return jsonify({
        "ok": True,
        "message": "Formulir Pengajuan Barang Persediaan berhasil dikirim dan disimpan!",
        "url": drive_file_url,
        "folder": drive_result.get("folder_path", ""),
    })


@app.route("/api/add/<target_key>", methods=["POST"])
def api_add_record(target_key):
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Restricted access!"}), 401

    if target_key not in TARGET_PERMISSION_MAP:
        return jsonify({"ok": False, "message": "Invalid target module!"}), 400

    mod_key, req_lvl = TARGET_PERMISSION_MAP[target_key]
    allowed = _has_perm(user, mod_key, req_lvl) or (
        target_key == "DB_Jadwal_Operasional" and _has_perm(user, "jadwal_tmb", "full")
    ) or (
        target_key == "DB_BMN_Dokumen" and any(_has_perm(user, mk, "full") for mk in [
            "aset_tutup_buku", "aset_calbmn", "aset_wasdal", "aset_rkbmn", "aset_manajemen_risiko", "aset_sisporja",
            "persediaan_tutup_buku", "persediaan_pipk"
        ])
    )
    if not allowed:
        display_key = mod_key.replace("DB_", "Data")
        return jsonify({"ok": False, "message": f"You need permission to access '{display_key}'."}), 403

    row_data = request.get_json(silent=True) or {}
    if target_key == "DB_Timeline":
        if not isinstance(row_data, dict):
            return jsonify({"ok": False, "message": "Invalid data format!"}), 400
        validation_error = _validate_timeline_data(row_data)
        if validation_error:
            return jsonify({"ok": False, "message": validation_error}), 400
        allowed_fields = {"Kegiatan", "Tahapan", "Tanggal Mulai", "Tanggal Selesai", "Keterangan"}
        row_data = {key: str(value or "").strip() for key, value in row_data.items() if key in allowed_fields}
        row_data["Tanggal"] = row_data["Tanggal Mulai"]
    ok, msg = db.append_record(target_key, row_data)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/delete/<target_key>", methods=["POST"])
def api_delete_record(target_key):
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Restricted access!"}), 401

    if target_key not in TARGET_PERMISSION_MAP:
        return jsonify({"ok": False, "message": "Invalid target module!"}), 400

    mod_key, req_lvl = TARGET_PERMISSION_MAP[target_key]
    allowed = _has_perm(user, mod_key, req_lvl) or (
        target_key == "DB_Jadwal_Operasional" and _has_perm(user, "jadwal_tmb", "full")
    ) or (
        target_key == "DB_BMN_Dokumen" and any(_has_perm(user, mk, "full") for mk in [
            "aset_tutup_buku", "aset_calbmn", "aset_wasdal", "aset_rkbmn", "aset_manajemen_risiko", "aset_sisporja",
            "persediaan_tutup_buku", "persediaan_pipk"
        ])
    )
    if not allowed:
        return jsonify({"ok": False, "message": f"You need permission to access '{mod_key}'."}), 403

    data = request.get_json(silent=True) or {}
    row_num = data.get("row_num")
    if not row_num:
        return jsonify({"ok": False, "message": "Invalid row number!"}), 400

    if target_key == "DB_BAST" and not _has_perm(user, "aset_tutup_buku", "full"):
        return jsonify({
            "ok": False,
            "message": "Penghapusan BAST terkait memerlukan hak penuh pada modul Tutup Buku.",
        }), 403

    is_bast_document = False
    if target_key == "DB_BMN_Dokumen":
        try:
            target_row_num = int(row_num)
        except (TypeError, ValueError):
            return jsonify({"ok": False, "message": "Invalid row number!"}), 400
        db._sync_snapshot(force=True)
        document = next(
            (
                row for row in db.get_tab_records(["DB_BMN_Dokumen"], include_row_num=True)
                if int(row.get("_row_num") or 0) == target_row_num
            ),
            None,
        )
        is_bast_document = bool(
            document
            and str(document.get("Group", "")).strip().lower() == "aset"
            and str(document.get("Sub Menu", "")).strip().lower() == "tutup buku"
            and str(document.get("Kategori Item", "")).strip().lower() == "bast"
        )
        if is_bast_document and (
            not _has_perm(user, "aset_tutup_buku", "full")
            or not _has_perm(user, "bast_otomatis", "full")
        ):
            return jsonify({
                "ok": False,
                "message": "Penghapusan dokumen BAST terkait memerlukan hak penuh pada modul BAST dan Tutup Buku.",
            }), 403

    if target_key == "DB_BAST" or is_bast_document:
        ok, msg = db.delete_bast_linked_record(target_key, row_num)
    else:
        ok, msg = db.delete_record(target_key, row_num)
    return jsonify({"ok": ok, "message": msg})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
