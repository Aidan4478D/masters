import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl

import requests

# -------------------------------------------------
# CAMERA CONFIG
# -------------------------------------------------
CAMERAS = [
    {
        "location": "Broadway @ Houston",
        "url": "https://webcams.nyctmc.org/api/cameras/5214cfe8-ccfc-42e9-8e2a-ff2865c1a518/image?t=1773349036633",
        "dates": {
            "2026-03-12",
            "2026-03-14",
            "2026-03-15",
            "2026-03-16",
            "2026-03-17",
        },
    },
    {
        "location": "Pelham Pkwy W_B @ Boston Rd",
        "url": "https://webcams.nyctmc.org/api/cameras/b2924000-6eb1-4449-b201-01c0653b6c68/image?t=1773349232213",
        "dates": {
            "2026-03-12",
            "2026-03-13",
            "2026-03-14",
            "2026-03-15",
            "2026-03-16",
            "2026-03-17",
        },
    },
    {
        "location": "Atlantic Ave @ Boerum Place",
        "url": "https://webcams.nyctmc.org/api/cameras/e64ec820-69c4-4cc9-b573-4d7d66c4a7eb/image?t=1773349814928",
        "dates": {
            "2026-03-20",
            "2026-03-21",
        },
    },
]

# -------------------------------------------------
# SETTINGS
# -------------------------------------------------
OUT_DIR = Path("../images/camera_images_direct")
SAMPLE_EVERY_SECONDS = 120.0

IMG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "Connection": "close",
    "Referer": "https://webcams.nyctmc.org/",
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_").lower()

def with_cache_buster(url: str) -> str:
    """Replace/add a timestamp query param so we don't get cached frames."""
    ts = str(int(time.time() * 1000))
    parts = list(urlparse(url))
    q = dict(parse_qsl(parts[4], keep_blank_values=True))
    q["t"] = ts
    parts[4] = urlencode(q)
    return urlunparse(parts)

def fetch_image_direct(url: str) -> requests.Response:
    """Fetch the latest camera image directly."""
    fresh_url = with_cache_buster(url)
    resp = requests.get(fresh_url, headers=IMG_HEADERS, timeout=30, stream=True)
    resp.raise_for_status()

    ctype = resp.headers.get("Content-Type", "").lower()
    if not ctype.startswith("image/"):
        body_preview = resp.text[:200] if "text" in ctype or ctype == "" else "<binary>"
        resp.close()
        raise ValueError(f"Expected image response, got Content-Type={ctype!r}, body preview={body_preview!r}")

    return resp

def save_stream_to(out_path: Path, resp: requests.Response) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)
    resp.close()

def should_capture_today(camera: dict, now: datetime) -> bool:
    today = now.strftime("%Y-%m-%d")
    return today in camera["dates"]

def build_output_path(base_dir: Path, camera: dict, now: datetime) -> Path:
    """
    Similar naming style to your previous script, but uses the location name
    in place of camera id.
    """
    timestamp = now.strftime("%Y_%m_%d__%H_%M_%S")
    location_slug = sanitize_filename(camera["location"])
    filename = f"{location_slug}__{timestamp}.jpg"
    return base_dir / location_slug / filename

# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
def main():
    print("[INFO] Starting direct camera capture loop.")
    print(f"[INFO] Saving under: {OUT_DIR.resolve()}")
    print(f"[INFO] Sampling every {SAMPLE_EVERY_SECONDS:.0f} seconds.")

    for cam in CAMERAS:
        print(f"[INFO] Camera: {cam['location']}")
        print(f"       Dates: {sorted(cam['dates'])}")
        print(f"       URL: {cam['url']}")

    while True:
        loop_start = time.time()
        now = datetime.now()

        for cam in CAMERAS:
            if not should_capture_today(cam, now):
                continue

            out_path = build_output_path(OUT_DIR, cam, now)

            try:
                resp = fetch_image_direct(cam["url"])
                save_stream_to(out_path, resp)
                print(f"[OK] {cam['location']} -> {out_path}")
            except Exception as e:
                print(f"[ERROR] {cam['location']}: {e}")

        elapsed = time.time() - loop_start
        sleep_s = max(0.0, SAMPLE_EVERY_SECONDS - elapsed)
        time.sleep(sleep_s)

if __name__ == "__main__":
    main()
