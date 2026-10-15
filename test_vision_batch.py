
from pathlib import Path
from video_to_bug.vision import analyze_frames

frames = [
    Path("output/frames/frame_0001.jpg"),
    Path("output/frames/frame_0050.jpg"),
]

output_file = Path("output/test_observations.json")

observations = analyze_frames(frames, output_file)

successful = sum(
    item["status"] == "success"
    for item in observations
)

print(f"\nSuccessful observations: {successful}/{len(observations)}")
print(f"Results saved to: {output_file}")
