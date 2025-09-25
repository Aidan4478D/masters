import os
import re
import time
from datetime import datetime

from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup


wanted_cameras = [
    # "6 Avenue @ West Houston Street",
    # "6 Avenue @ 58 Street",
    "7 Avenue @ 125 Street",
    "7 Avenue @ 34 Street"
]

API_KEY = os.environ.get('NYC511_KEY')
API_BASE = "https://511ny.org/api/getcameras?key="

IMG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://511ny.org/",
    "Accept-Language": "en-US,en;q=0.9",
}
HTML_HEADERS = {
    **IMG_HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
IMG_URL_REGEX = re.compile(
    r'https?://[^\s\'"]+?\.(?:jpg|jpeg|png|gif)(?:\?[^\s\'"]*)?',
    re.IGNORECASE
)


def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9._-]+', '_', name).strip('_').lower()

def name_matches(target, candidate):
    return target.lower() in candidate.lower()

def fetch_all_cameras(api_key):
    url = f"{API_BASE}{api_key}&format=json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    cams = r.json()
    if not isinstance(cams, list):
        raise ValueError("Unexpected API response (expected a list).")
    return cams



"""Try to fetch the camera URL directly as an image (content negotiation)."""
def try_fetch_image_direct(url, session: requests.Session):
    resp = session.get(url, timeout=30, stream=True, headers=IMG_HEADERS)
    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type", "").lower()
    if ctype.startswith("image/"):
        return resp

    # not an image; close and return None so we can fallback to scraping
    resp.close()
    return None


def save_stream_to(out_path: Path, resp: requests.Response):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)


def main():
    out_dir = Path("camera_images")
    session = requests.Session()

    cameras = fetch_all_cameras(API_KEY)

    # filter by wanted names
    selected = [c for c in cameras
                if c.get("Name") and any(name_matches(w, c["Name"]) for w in wanted_cameras)
                and c.get("Url") and c["Url"] != "Unknown"]

    if not selected:
        print("[INFO] No cameras matched your name filters.")
        return

    for cam in selected:
        cam_name = cam["Name"]
        cam_id = cam.get("ID", "camera")
        page_url = cam["Url"]

        # timestamp
        utc_timestamp = datetime.fromtimestamp(int(time.time())).strftime("%Y_%m_%d__%H_%M_%S")

        # filename
        base = f"{sanitize_filename(cam_name)}__{sanitize_filename(cam_id)}"
        out_path = out_dir / f"{base}" / utc_timestamp

        # direct image fetch (need Accept to be image/*)
        try:
            direct = try_fetch_image_direct(page_url, session)
            if direct is not None:
                out = out_path.with_suffix(".jpg")
                save_stream_to(out, direct)
                print(f"[OK] {cam_name} ({cam_id}) -> {out} [direct image]")
                continue
        except requests.HTTPError as he:
            print(f"[HTTP {he.response.status_code}] direct image failed for {cam_name}: {he}")
        except Exception as e:
            print(f"[ERROR] direct image failed for {cam_name}: {e}")


main()

