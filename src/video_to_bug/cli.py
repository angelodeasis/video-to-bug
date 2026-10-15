
import argparse
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import json
from datetime import datetime
import uuid
from pathlib import Path
from video_to_bug.selection import select_frames
from video_to_bug.vision import analyze_frames
from video_to_bug.report import generate_report

MODEL = "qwen2.5vl:7b"
OLLAMA_API = "http://localhost:11434"


def check_command(name):
    path = shutil.which(name)
    if path:
        print(f"[OK] {name}: {path}")
        return True

    print(f"[MISSING] {name}: not found on PATH")
    return False


def check_ollama():
    try:
        request = urllib.request.Request(
            f"{OLLAMA_API}/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))

        models = [
            model.get("name", "")
            for model in data.get("models", [])
        ]

        print("[OK] Ollama API is responding")

        if any(name == MODEL or name.startswith(MODEL + ":") for name in models):
            print(f"[OK] Vision model installed: {MODEL}")
            return True

        print(f"[MISSING] Vision model not installed: {MODEL}")
        print(f"         Install it with: ollama pull {MODEL}")
        return False

    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"[MISSING] Ollama API unavailable: {error}")
        print("         Start Ollama and try again.")
        return False


def extract_video_frames(video_path: Path, frames_dir: Path, interval: int = 2):
    """Extract one JPEG frame every `interval` seconds."""
    if interval < 1:
        raise ValueError("Frame interval must be at least 1 second.")

    frames_dir.mkdir(parents=True, exist_ok=False)

    duration_result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    duration = float(duration_result.stdout.strip())

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(video_path),
            "-vf", f"fps=1/{interval}",
            "-q:v", "2",
            str(frames_dir / "frame_%04d.jpg"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    frames = sorted(frames_dir.glob("frame_*.jpg"))

    if not frames:
        raise RuntimeError("FFmpeg completed but no frames were extracted.")

    return duration, frames

def main():
    parser = argparse.ArgumentParser(
        prog="video-to-bug",
        description=(
            "Turn screen recordings into evidence-based "
            "software bug reports."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version="video-to-bug 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor", help="Check required dependencies")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a screen recording",
    )
    analyze_parser.add_argument("video", nargs="?")

    args = parser.parse_args()

    if args.command == "doctor":
        print("Checking video-to-bug dependencies...\n")

        checks = [
            check_command("ffmpeg"),
            check_command("ffprobe"),
            check_command("ollama"),
            check_ollama(),
        ]

        print()
        if all(checks):
            print("All required dependencies are available.")
            return

        print("Some dependencies need attention.")
        sys.exit(1)

    elif args.command == "analyze":
        if not args.video:
            analyze_parser.error("provide a video path")

        from pathlib import Path

        video_path = Path(args.video).expanduser().resolve()

        if not video_path.exists():
            print(f"[ERROR] Video not found: {video_path}")
            sys.exit(1)

        if not video_path.is_file():
            print(f"[ERROR] Path is not a file: {video_path}")
            sys.exit(1)

        supported_extensions = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
        if video_path.suffix.lower() not in supported_extensions:
            print(
                f"[ERROR] Unsupported file extension: {video_path.suffix}\n"
                f"Supported extensions: {', '.join(sorted(supported_extensions))}"
            )
            sys.exit(1)

        print(f"[OK] Video found: {video_path}")
        print("[INFO] Video validation passed.")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"{timestamp}-{uuid.uuid4().hex[:6]}"

        run_dir = Path("output") / run_id
        run_dir.mkdir(parents=True, exist_ok=False)

        metadata = {
            "video_path": str(video_path),
            "run_id": run_id,
            "created_at": datetime.now().astimezone().isoformat(),
            "status": "initialized",
        }

        metadata_path = run_dir / "run.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"[OK] Run folder created: {run_dir}")
        print(f"[OK] Run metadata saved: {metadata_path}")
        frames_dir = run_dir / "frames"

        try:
            duration, frames = extract_video_frames(video_path, frames_dir)
        except (subprocess.CalledProcessError, ValueError, RuntimeError) as error:
            print(f"[ERROR] Frame extraction failed: {error}")
            metadata["status"] = "failed"
            metadata["error"] = str(error)
            metadata_path.write_text(
                json.dumps(metadata, indent=2) + "\n",
                encoding="utf-8",
            )
            sys.exit(1)

        metadata["status"] = "frames_extracted"
        metadata["duration_seconds"] = round(duration, 2)
        metadata["frame_count"] = len(frames)
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"[OK] Video duration: {duration:.2f} seconds")
        print(f"[OK] Frames extracted: {len(frames)}")
        print(f"[OK] Frames saved to: {frames_dir}")
        selected_file = run_dir / "selected_frames.txt"

        try:
            selected_frames = select_frames(
                frames_dir=frames_dir,
                output_file=selected_file,
            )
        except (FileNotFoundError, ValueError, OSError) as error:
            print(f"[ERROR] Frame selection failed: {error}")
            metadata["status"] = "failed"
            metadata["error"] = str(error)
            metadata_path.write_text(
                json.dumps(metadata, indent=2) + "\n",
                encoding="utf-8",
            )
            sys.exit(1)

        metadata["status"] = "frames_selected"
        metadata["selected_frame_count"] = len(selected_frames)
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"[OK] Selected frames saved to: {selected_file}")

        observations_file = run_dir / "observations.json"

        observations = analyze_frames(
            frame_paths=selected_frames,
            output_file=observations_file,
        )

        successful = sum(
            item["status"] == "success"
            for item in observations
        )

        metadata["status"] = "observations_analyzed"
        metadata["observation_count"] = len(observations)
        metadata["successful_observation_count"] = successful

        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"[OK] Observations saved to: {observations_file}")
        print(f"[OK] Successful observations: {successful}/{len(observations)}")
        report_file = run_dir / "report.md"

        try:
            generate_report(
                observations_file=observations_file,
                output_file=report_file,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"[ERROR] Report generation failed: {error}")
            metadata["status"] = "failed"
            metadata["error"] = str(error)
            metadata_path.write_text(
                json.dumps(metadata, indent=2) + "\n",
                encoding="utf-8",
            )
            sys.exit(1)

        metadata["status"] = "report_generated"
        metadata["report_path"] = str(report_file)
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"[OK] Your report is ready: {report_file}")


    else:
        parser.print_help()


if __name__ == "__main__":
    main()
