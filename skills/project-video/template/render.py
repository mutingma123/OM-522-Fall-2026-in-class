"""Render one video into an MP4 and a click-through HTML deck, and cut review stills.

Run it from this folder:

    pixi run render <video folder> check      run every scene without rendering (seconds)
    pixi run render <video folder> preview    720p at 15 frames per second, plus stills
    pixi run render <video folder> final      1080p at 30 frames per second, plus stills

Add --parts Part1Name Part2Name to render only those parts. That skips the joined MP4 and
the deck, which need every part.

The video folder holds scene.py, which lists its parts in order in PARTS. The outputs go
to <video folder>/output/<mode>/: <video folder>.mp4, deck/<video folder>.html, and
stills/ (one image per click and one contact sheet per part).
"""

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
MODES = {
    "check": ["--dry_run"],
    "preview": ["-r", "1280,720", "--fps", "15"],
    "final": ["-r", "1920,1080", "--fps", "30"],
}
RESOLUTION = {"preview": "720p15", "final": "1080p30"}

parser = argparse.ArgumentParser(description="Render a video and its deck.")
parser.add_argument("video", type=Path, help="the video's folder, e.g., spt-example")
parser.add_argument("mode", choices=list(MODES), nargs="?", default="preview")
parser.add_argument("--parts", nargs="+", help="render only these parts")
args = parser.parse_args()

video = (HERE / args.video).resolve()
scene_file = video / "scene.py"
if not scene_file.exists():
    sys.exit(f"No scene.py in {video}")

# Read PARTS = [...] from scene.py without running it.
parts = None
for node in ast.parse(scene_file.read_text(encoding="utf-8")).body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PARTS" for t in node.targets):
        parts = ast.literal_eval(node.value)
if not parts:
    sys.exit("scene.py must list its parts in order, e.g., PARTS = [\"Part1Setup\", \"Part2Result\"]")
scenes = args.parts or parts
unknown = [name for name in scenes if name not in parts]
if unknown:
    sys.exit(f"Not in PARTS: {unknown}")

name = video.name
out = video / "output" / args.mode
build = video / "build" / args.mode
checkpoints = build / "checkpoints"
slides = build / "slides"
shutil.rmtree(checkpoints, ignore_errors=True)
checkpoints.mkdir(parents=True)

env = dict(os.environ)
env["PYTHONPATH"] = os.pathsep.join([str(HERE), str(video), env.get("PYTHONPATH", "")])
env["CHECKPOINT_DIR"] = str(checkpoints)
env["SLIDES_DIR"] = str(slides)

# stdin is closed so manim never stops to ask a question.
command = [sys.executable, "-m", "manim", *MODES[args.mode], "--media_dir", str(build / "media"), str(scene_file), *scenes]
result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, cwd=video)

problems = "".join(path.read_text() for path in sorted(checkpoints.glob("*.problems.txt")))
if problems:
    print("\nProblems to fix:\n" + problems)
if result.returncode != 0:
    sys.exit(f"manim failed (exit code {result.returncode}). Read the error above.")
if args.mode == "check":
    if problems:
        sys.exit(1)
    print(f"Checked {', '.join(scenes)}: every scene ran, and nothing was rendered.")
    sys.exit(0)

clips = build / "media" / "videos" / "scene" / RESOLUTION[args.mode]


def ffmpeg(*arguments):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *arguments], check=True)


# One still per checkpoint, and one contact sheet of six stills per page per part.
for scene in scenes:
    stills = out / "stills" / scene
    shutil.rmtree(stills, ignore_errors=True)
    stills.mkdir(parents=True)
    records = json.loads((checkpoints / f"{scene}.json").read_text())
    for number, record in enumerate(records, start=1):
        record["path"] = stills / f"{number:02d}.png"
        # A checkpoint in a clip's last frame yields no image, so fall back a moment earlier.
        for seconds in (record["time"], max(0.0, record["time"] - 0.2)):
            ffmpeg("-ss", str(seconds), "-i", str(clips / f"{scene}.mp4"), "-frames:v", "1", str(record["path"]))
            if record["path"].exists():
                break
    for page in range(0, len(records), 6):
        sheet = Image.new("RGB", (1280, 1170), "#dddddd")
        draw = ImageDraw.Draw(sheet)
        for offset, record in enumerate(records[page : page + 6]):
            still = Image.open(record["path"])
            still.thumbnail((640, 360))
            x, y = (offset % 2) * 640, (offset // 2) * 390
            sheet.paste(still, (x, y + 30))
            draw.text((x + 10, y + 8), f"{page + offset + 1:02d} {record['name']}", fill="black")
        sheet.save(stills / f"sheet-{page // 6 + 1}.png")
    print(f"Stills for {scene}: {stills}")

if scenes != parts:
    print("Rendered some parts only, so the joined MP4 and the deck were skipped.")
    sys.exit(0)

# One continuous MP4. Every part has the same size and frame rate, so the streams are copied.
out.mkdir(parents=True, exist_ok=True)
listing = build / "parts.txt"
listing.write_text("".join(f"file '{(clips / f'{scene}.mp4').as_posix()}'\n" for scene in scenes))
ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(out / f"{name}.mp4"))

# The deck. --offline copies reveal.js next to the page, so it plays without internet.
deck = out / "deck"
shutil.rmtree(deck, ignore_errors=True)
deck.mkdir(parents=True)
subprocess.run(
    [sys.executable, "-m", "manim_slides", "convert", "--folder", str(slides), "--to", "html", "--offline", *scenes, str(deck / f"{name}.html")],
    check=True,
)
count = sum(len(json.loads((slides / f"{scene}.json").read_text())["slides"]) for scene in scenes)
print(f"\nVideo: {out / f'{name}.mp4'}")
print(f"Deck ({count} slides): {deck / f'{name}.html'}")
print("Open the deck in a browser. The right arrow advances one click.")
