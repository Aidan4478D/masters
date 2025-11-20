import os
import re
import time
from datetime import datetime

from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

wanted_cameras = {
    # Manhattan
    "manhattan": [
        "3 Avenue @ 23 Street", # front facing
        "9 Avenue @ 49 Street", # front facing
        "Houston Street @ Bowery Street", # front facing
        "Church Street @ Park Pl", # side facing
        "Canal Street @ Baxter Street", # front and back

        "Amsterdam Avenue @ 125 Street",
    ],
    "bronx": [
        # might have to resort to other screen capture for these
        "Fordham Road @ Hughes Avenue", # very not ideal
        "Lenox Avenue @ 135 Street",
    ],
    "queens": [
        "Hillside Avenue @ Little Neck Parkway", # bad quality
    ],
    "brooklyn": [
        # brooklyn
        "Atlantic Avenue @ BQE",
        "Atlantic Avenue @ Vanderbilt Avenue", # looks like highway
        "Ocean Parkway @ Ditmas Avenue",
    ],
    "staten_island": [

    ]

    # "6 Avenue @ West Houston Street",
    # "6 Avenue @ 58 Street",
    # "7 Avenue @ 125 Street",
    # "7 Avenue @ 34 Street"
}

API_KEY = os.environ.get('NYC511_KEY')
API_BASE = "https://511ny.org/api/getcameras?key="

IMG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://511ny.org/",
    "Accept-Language": "en-US,en;q=0.9",

    # hard no-cache
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",

    # avoid long-lived keep-alive caches/proxies
    "Connection": "close",
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
    url = with_cache_buster(url)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    cams = r.json()
    if not isinstance(cams, list):
        raise ValueError("Unexpected API response (expected a list).")
    return cams



def with_cache_buster(url: str) -> str:
    """Append a _t=timestamp query param so caches treat it as unique."""
    ts = str(int(time.time()))
    parts = list(urlparse(url))
    q = dict(parse_qsl(parts[4], keep_blank_values=True))
    q["_t"] = ts
    parts[4] = urlencode(q)
    return urlunparse(parts)



"""Try to fetch the camera URL directly as an image (content negotiation)."""
def try_fetch_image_direct(url):
    # unique URL each time
    url = with_cache_buster(url)

    # fresh TCP/TLS connection per request (no session pooling)
    resp = requests.get(url, timeout=30, stream=True, headers=IMG_HEADERS)
    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type", "").lower()
    if ctype.startswith("image/"):
        return resp
    resp.close()

    return None


def save_stream_to(out_path: Path, resp: requests.Response):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)

def wanted_maps(wanted_cameras):
    pairs = []
    for borough, names in wanted_cameras.items():
        for nm in names:
            pairs.append((nm, borough))

    return pairs

def main():
    out_dir = Path("camera_images")
    session = requests.Session()

    cameras = fetch_all_cameras(API_KEY)

    # filter by wanted names
    wanted_pairs = wanted_maps(wanted_cameras)

    selected = []
    for c in cameras:
        nm = c.get("Name") or ""
        url = c.get("Url")
        if not nm or not url or url == "Unknown":
            continue
        for wanted_name, borough in wanted_pairs:
            if name_matches(wanted_name, nm):
                selected.append((borough, c))
                break

    if not selected:
        print("[INFO] No cameras matched your name filters.")
        return

    while True: 
        loop_start = time.time()

        for borough, cam in selected:
            cam_name = cam["Name"]
            cam_id = cam.get("ID", "camera")
            page_url = cam["Url"]

            # timestamp
            utc_timestamp = datetime.fromtimestamp(int(time.time())).strftime("%Y_%m_%d__%H_%M_%S")

            # filename
            base = f"{sanitize_filename(cam_name)}__{sanitize_filename(cam_id)}"
            out_path = out_dir / sanitize_filename(borough) / f"{base}" / utc_timestamp

            # direct image fetch (need Accept to be image/*)
            try:
                direct = try_fetch_image_direct(page_url)
                if direct is not None:
                    out = out_path.with_suffix(".jpg")
                    save_stream_to(out, direct)
                    print(f"[OK] {cam_name} ({cam_id}) -> {out} [direct image]")
                    continue
            except requests.HTTPError as he:
                print(f"[HTTP {he.response.status_code}] direct image failed for {cam_name}: {he}")
            except Exception as e:
                print(f"[ERROR] direct image failed for {cam_name}: {e}")

        elapsed = time.time() - loop_start
        sleep_s = max(0.0, 120.0 - elapsed)
        time.sleep(sleep_s)

main()

