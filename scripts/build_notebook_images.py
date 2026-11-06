"""Make the phone-sized pictures and videos the notebook uses.

Reads the originals in static/images and writes smaller copies to static/img, plus
static/img/manifest.json (each picture's width and height, so pages can reserve space).
Run it again after changing a source picture:

    python scripts/build_notebook_images.py

Needs Pillow. Videos need ffmpeg on the path (skipped with a note if it is missing).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static" / "images"
OUT = ROOT / "static" / "img"

# (source relative to static/images, output relative to static/img, max width)
PICTURES: list[tuple[str, str, int]] = []

PICTURES += [(f"Work/{n}.webp", f"work/{o}.webp", 240) for n, o in [
    ("Denali", "denali"), ("ScribbleScan", "scribblescan"), ("2ndChair", "2ndchair"),
    ("Tech", "tech"), ("TCGC", "tcgc"), ("GTC", "gtc"), ("PTC", "ptc")]]
PICTURES += [(f"projects/ScribbleScan/{n}.webp", f"scribblescan/{o}.webp", 900) for n, o in [
    ("Feb7", "feb7"), ("Feb8", "feb8"), ("Mar12", "mar12"), ("Apr28", "apr28"),
    ("Jun25", "jun25"), ("Jul1", "jul1")]]
for version, count in (("v1", 8), ("v2", 6), ("v3", 3)):
    PICTURES += [(f"projects/this_website/{version}/{i}.webp", f"site/{version}-{i}.webp", 800) for i in range(1, count + 1)]
PICTURES += [(f"projects/this_website/v3/themes/{n}.webp", f"site/theme-{n}.webp", 420) for n in (
    "original", "clouds", "islands", "lily-pads", "planets", "postcards", "vinyl")]
PICTURES += [(f"hobbies/gaming/{n}.webp", f"games/{n.lower()}.webp", 260) for n in (
    "Cyberpunk", "HighOnLife", "MKWii", "Subnautica", "SubnauticaBZ", "EdithFinch", "SoT", "Minecraft", "NMS",
    "Portal", "Portal2", "Trackmania", "Valorant", "Apex", "Firewatch", "OuterWilds", "Titanfall", "Titanfall2",
    "road96", "ForeverSkies")]
PICTURES += [
    ("hobbies/3DModelIcon.webp", "hobbies/model-icon.webp", 200),
    ("hobbies/spin.webp", "tennis/spin.webp", 600),
    ("hobbies/Forehand.webp", "tennis/forehand.webp", 723),
    ("education/UPSCampus.webp", "school/upscampus.webp", 800),
    ("education/UPSTennis.webp", "school/upstennis.webp", 710),
    ("education/MaroonSociety.webp", "school/maroonsociety.webp", 300),
    ("education/GHS.webp", "school/ghs.webp", 800),
    ("education/BMS.webp", "school/bms.webp", 800),
    ("education/AES.webp", "school/aes.webp", 800),
    ("projects/digital_planner/Sprint1Thumb.webp", "planner/old-poster.webp", 720),
]

# (source, output, max width)
VIDEOS = [
    ("projects/digital_planner/DP_Old.mp4", "planner/old.mp4", 720),
    ("projects/digital_planner/DP_New.mp4", "planner/new.mp4", 720),
]


def build_pictures() -> dict[str, list[int]]:
    sizes: dict[str, list[int]] = {}
    for source, output, width in PICTURES:
        with Image.open(SRC / source) as image:
            image = image.convert("RGBA") if image.mode in ("P", "LA") else image
            if image.width > width:
                image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
            target = OUT / output
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, "WEBP", quality=80, method=6)
            sizes[output] = [image.width, image.height]
    return sizes


def video_size(ffmpeg: str, path: Path) -> list[int]:
    report = subprocess.run([ffmpeg, "-i", str(path)], capture_output=True, text=True).stderr
    match = re.search(r"Video:.*?(\d{3,4})x(\d{3,4})", report)
    return [int(match.group(1)), int(match.group(2))]


def build_videos(sizes: dict[str, list[int]]) -> None:
    ffmpeg = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found (set FFMPEG or install it); videos skipped")
        return
    for source, output, width in VIDEOS:
        target = OUT / output
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error", "-i", str(SRC / source),
            "-vf", f"scale={width}:-2", "-c:v", "libx264", "-crf", "30", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(target),
        ], check=True)
        sizes[output] = video_size(ffmpeg, target)
    # the second video has no poster of its own: use a frame from it
    frame = OUT / "planner/new-poster.png"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", "2", "-i", str(OUT / "planner/new.mp4"), "-frames:v", "1", str(frame)], check=True)
    with Image.open(frame) as image:
        image.save(OUT / "planner/new-poster.webp", "WEBP", quality=80)
        sizes["planner/new-poster.webp"] = [image.width, image.height]
    frame.unlink()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = build_pictures()
    build_videos(sizes)
    manifest = OUT / "manifest.json"
    if manifest.exists():  # keep video sizes from an earlier run when ffmpeg is missing
        sizes = {**json.loads(manifest.read_text()), **sizes}
    manifest.write_text(json.dumps(dict(sorted(sizes.items())), indent=1) + "\n")
    total = sum(path.stat().st_size for path in OUT.rglob("*") if path.is_file())
    print(f"{len(sizes)} files, {total / 1_000_000:.1f} MB in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
