from pathlib import Path
from video_to_bug.vision import analyze_frame

frame = Path("output/frames/frame_0050.jpg")

if not frame.exists():
    raise FileNotFoundError(f"Test frame not found: {frame}")

print(f"Analyzing {frame} with the local vision model...\n")
print(analyze_frame(frame))
