import time, os
from datetime import datetime
from pathlib import Path
import mss, mss.tools

SAVE_DIR = Path(r"\\wsl.localhost\Ubuntu\home\aidan\repos\masters\scripts\screenshots")
INTERVAL_S = 10

# Capture a region (left, top, width, height). Use None to capture full screen.
REGION = {"left": 320, "top": 290, "width": 1275, "height": 810}

SAVE_DIR.mkdir(parents=True, exist_ok=True)

with mss.mss() as sct:
    # use the region 
    # for full screen, pass sct.monitors[1]
    region = REGION
    while True:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out = SAVE_DIR / f"screenshot_{ts}.png"
        shot = sct.grab(region)
        mss.tools.to_png(shot.rgb, shot.size, output=str(out))
        print(f"Saved {out}")
        time.sleep(INTERVAL_S)

