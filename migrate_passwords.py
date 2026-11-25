"""
migrate_passwords.py
====================
One-shot script to migrate all plain-text passwords in CFG_Users to
werkzeug pbkdf2 hashes.

Usage:
    python migrate_passwords.py           # dry-run (shows what would change)
    python migrate_passwords.py --commit  # actually write to Google Sheet

Run this ONCE after deploying the new auth code.  Users who log in after
the migration will also be rehashed automatically on first login if their
password is still plain-text (belt-and-suspenders approach).
"""

import sys
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DRY_RUN = "--commit" not in sys.argv

# ── import the DB ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_service import SheetsDB

db = SheetsDB()
if not db.connected:
    print(f"[ERROR] Database tidak terhubung: {db.last_error}")
    sys.exit(1)

ws = db._find_ws(["CFG_Users"])
if not ws:
    print("[ERROR] Tab CFG_Users tidak ditemukan.")
    sys.exit(1)

all_vals = ws.get_all_values()
if not all_vals:
    print("[INFO] CFG_Users kosong.")
    sys.exit(0)

headers = [h.strip() for h in all_vals[0]]
nip_idx   = headers.index("NIP")          if "NIP"           in headers else 0

# Detect which column holds the password (old "Password" or new "Password_Hash")
if "Password_Hash" in headers:
    pwd_col = "Password_Hash"
elif "Password" in headers:
    pwd_col = "Password"
else:
    print("[ERROR] Kolom Password tidak ditemukan.")
    sys.exit(1)

pwd_idx = headers.index(pwd_col)

migrated = 0
already_hashed = 0
skipped_empty = 0

for r_i, row in enumerate(all_vals[1:], start=2):
    padded = row + [""] * (len(headers) - len(row))
    nip   = padded[nip_idx].strip()
    stored = padded[pwd_idx].strip()

    if not stored:
        skipped_empty += 1
        print(f"  [SKIP] Row {r_i} NIP={nip} — password kosong")
        continue

    if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
        already_hashed += 1
        print(f"  [OK]   Row {r_i} NIP={nip} — sudah di-hash")
        continue

    hashed = generate_password_hash(stored)
    if DRY_RUN:
        print(f"  [DRY]  Row {r_i} NIP={nip} — akan di-hash (plain={stored!r})")
    else:
        ws.update_cell(r_i, pwd_idx + 1, hashed)
        print(f"  [DONE] Row {r_i} NIP={nip} — berhasil di-hash")
    migrated += 1

print()
print(f"Hasil: {migrated} akan/sudah dimigrasikan, "
      f"{already_hashed} sudah aman, {skipped_empty} kosong.")
if DRY_RUN and migrated:
    print("Jalankan ulang dengan --commit untuk menerapkan perubahan ke Google Sheet.")
