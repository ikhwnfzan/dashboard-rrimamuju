import os
import re
import json
import time
import xml.etree.ElementTree as ET
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_YT_HANDLE = "@LPPRRIMamuju"
DEFAULT_DRIVE_FOLDER_ID = "1CwKdnqac1S3MrZApAzPpZKvrRZ8r8iZn"

_MEDIA_CACHE = {"youtube": (0, None), "flyers": (0, None), "channel_id": None}
MEDIA_TTL = 300


def _extract_folder_id(val):
    val = str(val or "").strip()
    if "/folders/" in val:
        return val.split("/folders/")[1].split("?")[0].split("/")[0]
    return val or DEFAULT_DRIVE_FOLDER_ID


def _load_sa_credentials():
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    for candidate in [
        os.path.join(BASE_DIR, "service_account.json"),
        os.path.join(BASE_DIR, "service_account.json.json"),
        "service_account.json",
    ]:
        if os.path.exists(candidate):
            return Credentials.from_service_account_file(candidate, scopes=scopes)

    raw_env = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    if raw_env:
        if (raw_env.startswith("'") and raw_env.endswith("'")) or (raw_env.startswith('"') and raw_env.endswith('"')):
            raw_env = raw_env[1:-1].strip()
        try:
            info = json.loads(raw_env)
        except json.JSONDecodeError:
            info = json.loads(raw_env.replace("\\r\\n", "\\n").replace("\r\n", "\\n").replace("\n", "\\n"))
        return Credentials.from_service_account_info(info, scopes=scopes)
    return None


class MediaFeedService:
    def __init__(self):
        self.yt_handle = os.getenv("YOUTUBE_HANDLE", DEFAULT_YT_HANDLE).strip()
        self.yt_channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
        self.drive_folder_id = _extract_folder_id(os.getenv("FLYER_DRIVE_FOLDER_ID", DEFAULT_DRIVE_FOLDER_ID))

    def _resolve_youtube_channel_id(self):
        if self.yt_channel_id:
            return self.yt_channel_id
        if _MEDIA_CACHE["channel_id"]:
            return _MEDIA_CACHE["channel_id"]

        handle = self.yt_handle if self.yt_handle.startswith("@") else f"@{self.yt_handle}"
        try:
            resp = requests.get(f"https://www.youtube.com/{handle}", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            if resp.ok:
                m = re.search(r'"externalId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"', resp.text) or re.search(r'channel_id=(UC[a-zA-Z0-9_-]{22})', resp.text)
                if m:
                    _MEDIA_CACHE["channel_id"] = m.group(1)
                    return m.group(1)
        except Exception:
            pass
        return None

    def get_youtube_feed(self, force=False):
        now = time.time()
        cached_ts, cached_val = _MEDIA_CACHE["youtube"]
        if not force and cached_val and (now - cached_ts < MEDIA_TTL):
            return cached_val

        cid = self._resolve_youtube_channel_id()
        videos = []
        if cid:
            try:
                r = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", timeout=8)
                if r.ok:
                    root = ET.fromstring(r.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
                    for entry in root.findall("atom:entry", ns)[:6]:
                        vid_el = entry.find("yt:videoId", ns)
                        title_el = entry.find("atom:title", ns)
                        pub_el = entry.find("atom:published", ns)
                        if vid_el is not None and vid_el.text:
                            vid = vid_el.text.strip()
                            videos.append({
                                "video_id": vid,
                                "title": title_el.text.strip() if title_el is not None else "Siaran LPP RRI Mamuju",
                                "published": (pub_el.text or "")[:10] if pub_el is not None else "",
                                "url": f"https://www.youtube.com/watch?v={vid}",
                                "embed_url": f"https://www.youtube.com/embed/{vid}?rel=0",
                                "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                            })
            except Exception:
                pass

        if not videos:
            videos = [
                {
                    "video_id": "vACkSb0QIIU",
                    "title": "Bangga Ber-indonesia lewat Gaya Hidup | Pro 2 RRI Mamuju",
                    "published": "2026-11-16",
                    "url": "https://www.youtube.com/watch?v=vACkSb0QIIU",
                    "embed_url": "https://www.youtube.com/embed/vACkSb0QIIU?rel=0",
                    "thumbnail": "https://i.ytimg.com/vi/vACkSb0QIIU/hqdefault.jpg",
                }
            ]

        result = {
            "channel_url": f"https://www.youtube.com/{self.yt_handle}",
            "channel_id": cid or "",
            "live_embed_url": f"https://www.youtube.com/embed/live_stream?channel={cid}" if cid else videos[0]["embed_url"],
            "videos": videos,
        }
        _MEDIA_CACHE["youtube"] = (now, result)
        return result

    def get_drive_flyers(self, force=False):
        now = time.time()
        cached_ts, cached_val = _MEDIA_CACHE["flyers"]
        if not force and cached_val and (now - cached_ts < MEDIA_TTL):
            return cached_val

        flyers = []
        folder_id = self.drive_folder_id
        creds = _load_sa_credentials()
        if creds:
            try:
                service = build("drive", "v3", credentials=creds, cache_discovery=False)
                query = f"'{folder_id}' in parents and trashed = false and mimeType contains 'image/'"
                res = service.files().list(q=query, pageSize=15, orderBy="createdTime desc", fields="files(id, name, webViewLink, createdTime)").execute()
                for f in res.get("files", []):
                    fid = f["id"]
                    flyers.append({
                        "id": fid,
                        "name": f.get("name", "Flyer Siaran"),
                        "image_url": f"https://drive.google.com/thumbnail?id={fid}&sz=w1000",
                        "view_url": f.get("webViewLink") or f"https://drive.google.com/file/d/{fid}/view",
                    })
            except Exception:
                pass

        if not flyers:
            try:
                resp = requests.get(f"https://drive.google.com/embeddedfolderview?id={folder_id}#grid", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                if resp.ok:
                    entries = re.findall(r'href="https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/view[^"]*"[^>]*>.*?<div class="flip-entry-title">([^<]+)</div>', resp.text, re.DOTALL)
                    seen = set()
                    for fid, raw_name in entries:
                        if fid not in seen:
                            seen.add(fid)
                            flyers.append({
                                "id": fid,
                                "name": raw_name.strip(),
                                "image_url": f"https://drive.google.com/thumbnail?id={fid}&sz=w1000",
                                "view_url": f"https://drive.google.com/file/d/{fid}/view",
                            })
            except Exception:
                pass

        result = {"folder_url": f"https://drive.google.com/drive/folders/{folder_id}", "items": flyers[:12]}
        _MEDIA_CACHE["flyers"] = (now, result)
        return result

    def clear_cache(self):
        _MEDIA_CACHE["youtube"] = (0, None)
        _MEDIA_CACHE["flyers"] = (0, None)
