# Verify palm pipeline outputs vary per image (not hard-coded).
import hashlib
import json
import sys

sys.path.insert(0, r"C:\Users\ASUS\Desktop\Palmistry\backend")

from app.services.palm_analysis.pipeline import analyze_palm_image

DATASET = r"C:\Users\ASUS\Desktop\Palmistry\dataset\Hands and palm images dataset\Hands\Hands"
IMAGES = [DATASET + "\\Hand_0003272.jpg", DATASET + "\\Hand_0003285.jpg"]

KEYS = [
    ("hand.detected_handedness", lambda a: a["hand"]["detected_handedness"]),
    ("hand.handedness_confidence", lambda a: a["hand"]["handedness_confidence"]),
    ("shape.element", lambda a: a["palm_shape"]["element"]),
    ("shape.aspect_ratio", lambda a: a["palm_shape"]["aspect_ratio"]),
    ("shape.finger_to_palm_ratio", lambda a: a["palm_shape"]["finger_to_palm_ratio"]),
    ("finger.2d4d", lambda a: a["finger_structure"]["digit_ratio_2d_4d"]),
    ("finger.thumb_angle", lambda a: a["finger_structure"]["thumb_angle_degrees"]),
    ("lines.life.confidence", lambda a: a["lines"][0]["confidence"]),
    ("lines.life.curvature", lambda a: a["lines"][0]["curvature"]),
    ("lines.life.first_coord", lambda a: tuple(a["lines"][0]["coordinates"][0].values())),
    ("lines.head.confidence", lambda a: a["lines"][1]["confidence"]),
    ("lines.heart.confidence", lambda a: a["lines"][2]["confidence"]),
    ("lines.fate.confidence", lambda a: a["lines"][3]["confidence"]),
    ("lines.sun.confidence", lambda a: a["lines"][4]["confidence"]),
    ("mounts.jupiter.score", lambda a: a["mounts"][0]["score"]),
    ("mounts.venus.score", lambda a: a["mounts"][4]["score"]),
    ("metadata.overall_confidence", lambda a: a["metadata"]["overall_confidence"]),
    ("metadata.original_resolution", lambda a: a["metadata"]["original_resolution"]),
    ("landmark0.wrist_px", lambda a: (a["hand"]["landmarks"][0]["x"], a["hand"]["landmarks"][0]["y"])),
    ("landmark12.middle_tip", lambda a: (a["hand"]["landmarks"][12]["x"], a["hand"]["landmarks"][12]["y"])),
]

results = {}
for path in IMAGES:
    with open(path, "rb") as f:
        data = f.read()
    analysis = analyze_palm_image(data, enforce_palmar=False)
    results[path] = analysis

print(f"{'metric':32s}  {'img A (...3272)':>28s}  {'img B (...3285)':>28s}  differ?")
print("-" * 105)
a, b = results[IMAGES[0]], results[IMAGES[1]]
n_differ = 0
for name, fn in KEYS:
    try:
        va, vb = fn(a), fn(b)
        diff = va != vb
        n_differ += int(diff)
        print(f"{name:32s}  {str(va):>28s}  {str(vb):>28s}  {'YES' if diff else 'no'}")
    except Exception as e:
        print(f"{name:32s}  ERROR: {e}")

print("-" * 105)
print(f"{n_differ}/{len(KEYS)} metrics differ between the two images")

# Sanity: pixel-level content hashes differ
for path in IMAGES:
    with open(path, "rb") as f:
        print(path.split(chr(92))[-1], "file_sha1:", hashlib.sha1(f.read()).hexdigest()[:12])

# Full JSON of image A lines for eyeball check
print("\n=== Image A line summary ===")
for line in a["lines"]:
    print(f"  {line['name']:12s} conf={line['confidence']:.2f} curvature={line['curvature']:.2f} "
          f"continuity={line['continuity']:12s} variation={line['variation_type']}")
print("\n=== Image A mounts ===")
for m in a["mounts"]:
    print(f"  {m['name']:14s} score={m['score']:.2f} prominence={m['prominence']}")
