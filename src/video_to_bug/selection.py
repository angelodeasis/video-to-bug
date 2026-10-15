
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def visual_difference(first_path: Path, second_path: Path) -> float:
    """Measure the average pixel difference between two frames."""
    with Image.open(first_path) as first, Image.open(second_path) as second:
        first = first.convert("RGB").resize((160, 100))
        second = second.convert("RGB").resize((160, 100))
        difference = ImageChops.difference(first, second)
        return sum(ImageStat.Stat(difference).mean) / 3


def select_frames(
    frames_dir: Path,
    output_file: Path,
    max_changed: int = 10,
    coverage_count: int = 8,
) -> list[Path]:
    """Select visually changed frames plus evenly spaced timeline coverage."""
    frames = sorted(frames_dir.glob("frame_*.jpg"))

    if not frames:
        raise FileNotFoundError(f"No frames found in {frames_dir}")

    if max_changed < 0 or coverage_count < 2:
        raise ValueError("max_changed must be nonnegative and coverage_count at least 2.")

    scores = {}

    for previous, current in zip(frames, frames[1:]):
        number = int(current.stem.split("_")[1])
        scores[number] = visual_difference(previous, current)

    # Select frames with the largest visual changes.
    most_changed = sorted(
        scores,
        key=scores.get,
        reverse=True,
    )[:max_changed]

    # Add evenly distributed frames, including the start and end.
    last_index = len(frames) - 1
    coverage_indices = {
        round(i * last_index / (coverage_count - 1))
        for i in range(coverage_count)
    }
    coverage_frames = {
        int(frames[index].stem.split("_")[1])
        for index in coverage_indices
    }

    selected_numbers = sorted(set(most_changed) | coverage_frames)
    selected_frames = [
        frame
        for frame in frames
        if int(frame.stem.split("_")[1]) in selected_numbers
    ]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as output:
        output.write("Selected frames for review\n")
        output.write(
            "Selection uses visual changes and evenly spaced timeline coverage.\n\n"
        )

        for frame in selected_frames:
            number = int(frame.stem.split("_")[1])
            output.write(frame.name)

            if number in scores:
                output.write(f" — change score: {scores[number]:.1f}")

            output.write("\n")

    print(f"Found {len(frames)} frames.")
    print(f"Selected {len(selected_frames)} frames.")
    print(f"Saved list to {output_file}")

    return selected_frames
