import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from sheets_service import SheetsDB

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


@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", station=STATION_INFO, user=user)


@app.route("/api/board")
def api_board():
    user = session.get("user")
    payload = {
        "connected": db.connected,
        "status_msg": "Live Google Sheets" if db.connected else (db.last_error or "Mode Demo"),
        "server_time": datetime.now().strftime("%d %b %Y • %H:%M WITA"),
        "authenticated": bool(user),
        "user": user,
        "timeline": db.get_timeline(),
        "dialogs": db.get_agenda_setting(),
        "archive": db.get_records("Arsip"),
        "planner": db.get_records("Planner") if user else [],
        "siaran": db.get_records("Siaran") if user else [],
        "info_pegawai": db.get_records("Info_Pegawai") if user else [],
    }
    return jsonify(payload)


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip().lower()
    pin = str(data.get("pin", "")).strip()

    users = db.get_records("Users")
    for u in users:
        if str(u.get("Username", "")).strip().lower() == username and str(u.get("PIN", "")).strip() == pin:
            user_info = {
                "username": u.get("Username"),
                "nama": u.get("Nama"),
                "divisi": u.get("Divisi"),
                "role": u.get("Role", "Staff")
            }
            session["user"] = user_info
            return jsonify({"ok": True, "user": user_info})

    return jsonify({"ok": False, "message": "Username atau PIN salah."}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify({"ok": True})


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    db.clear_cache()
    return jsonify({"ok": True, "message": "Cache diperbarui."})


@app.route("/api/setup-sheets", methods=["POST"])
def api_setup_sheets():
    user = session.get("user")
    if not user or str(user.get("role", "")).lower() != "admin":
        return jsonify({"ok": False, "message": "Hanya Admin yang dapat melakukan inisialisasi sheet."}), 403
    ok, msg = db.init_missing_tabs()
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/add/<target_key>", methods=["POST"])
def api_add_record(target_key):
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "message": "Silakan login pegawai terlebih dahulu."}), 401

    allowed = {"Timeline", "Agenda_Setting", "Planner", "Siaran", "Arsip", "Info_Pegawai"}
    if target_key not in allowed:
        return jsonify({"ok": False, "message": "Target tab tidak valid."}), 400

    row_data = request.get_json(silent=True) or {}
    ok, msg = db.append_record(target_key, row_data)
    return jsonify({"ok": ok, "message": msg})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
