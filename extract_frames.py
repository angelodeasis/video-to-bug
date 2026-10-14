from pathlib import Path
import subprocess
import json

VIDEO_PATH = Path("samples/testvid.mov")
OUTPUT_DIR = Path("output/frames")
INTERVAL_SECONDS = 2


def get_video_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def extract_frames(video_path: Path, output_dir: Path, interval: int) -> None:
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    duration = get_video_duration(video_path)

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(video_path),
            "-vf", f"fps=1/{interval}",
            "-q:v", "2",
            str(output_dir / "frame_%04d.jpg"),
        ],
        check=True,
    )

    frame_count = len(list(output_dir.glob("frame_*.jpg")))
    print(f"Video duration: {duration:.2f} seconds")
    print(f"Frames extracted: {frame_count}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    extract_frames(VIDEO_PATH, OUTPUT_DIR, INTERVAL_SECONDS)
