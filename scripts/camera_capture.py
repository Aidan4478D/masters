import time, os
from datetime import datetime
from pathlib import Path
import mss, mss.tools

# SAVE_DIR = Path(r"C:\Users\Aidan\Pictures\screen_caps")
INTERVAL_S = 10
REGION = {"left": 300, "top": 200, "width": 640, "height": 480}
SAVE_DIR.mkdir(parents=True, exist_ok=True)

with mss.mss() as sct:
    region = REGION
    while True:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out = SAVE_DIR / f"screenshot_{ts}.png"
        shot = sct.grab(region)
        mss.tools.to_png(shot.rgb, shot.size, output=str(out))
        print(f"Saved {out}")
        time.sleep(INTERVAL_S)

