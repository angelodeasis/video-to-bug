
from pathlib import Path
from PIL import Image, ImageDraw

frames_dir = Path("output/frames")
output_path = Path("output/contact_sheet.jpg")

frames = sorted(frames_dir.glob("frame_*.jpg"))

if not frames:
    raise SystemExit("No extracted frames found.")

thumb_width = 240
thumb_height = 180
label_height = 28
columns = 4
rows = (len(frames) + columns - 1) // columns

sheet = Image.new(
    "RGB",
    (columns * thumb_width, rows * (thumb_height + label_height)),
    "white",
)
draw = ImageDraw.Draw(sheet)

for index, frame_path in enumerate(frames):
    with Image.open(frame_path) as image:
        image.thumbnail((thumb_width, thumb_height))
        x = (index % columns) * thumb_width
        y = (index // columns) * (thumb_height + label_height)

        sheet.paste(image, (x, y))
        timestamp = index * 2
        draw.text(
            (x + 5, y + thumb_height + 5),
            f"{frame_path.name} | ~{timestamp}s",
            fill="black",
        )

output_path.parent.mkdir(parents=True, exist_ok=True)
sheet.save(output_path, quality=90)

print(f"Frames included: {len(frames)}")
print(f"Contact sheet: {output_path}")
