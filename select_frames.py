
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

FRAME_DIR = Path("output/frames")
OUTPUT_FILE = Path("output/selected_frames.txt")

# Always retain these frames, including the end where the error appeared.
PRIORITY_FRAMES = {1, 11, 15, 19, 29, 33, 37, 41, 45, 48, 50, 52, 55}


def visual_difference(first_path, second_path):
    with Image.open(first_path) as first, Image.open(second_path) as second:
        first = first.convert("RGB").resize((160, 100))
        second = second.convert("RGB").resize((160, 100))
        difference = ImageChops.difference(first, second)
        return sum(ImageStat.Stat(difference).mean) / 3


frames = sorted(FRAME_DIR.glob("frame_*.jpg"))
if not frames:
    raise SystemExit(f"No frames found in {FRAME_DIR}")

scores = {}
for previous, current in zip(frames, frames[1:]):
    number = int(current.stem.split("_")[1])
    scores[number] = visual_difference(previous, current)

# Pick the 10 frames with the largest visual changes.
most_changed = sorted(scores, key=scores.get, reverse=True)[:10]
selected = sorted(PRIORITY_FRAMES | set(most_changed))

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_FILE.open("w", encoding="utf-8") as output:
    output.write("Selected frames for review\n")
    output.write("Selection uses visual change plus fixed timeline checkpoints.\n\n")
    for number in selected:
        output.write(f"frame_{number:04d}.jpg")
        if number in scores:
            output.write(f" — change score: {scores[number]:.1f}")
        output.write("\n")

print(f"Found {len(frames)} frames.")
print(f"Selected {len(selected)} frames.")
print(f"Saved list to {OUTPUT_FILE}")
print("\nSelected frame numbers:")
print(", ".join(str(n) for n in selected))
