
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_API = "http://localhost:11434"
MODEL = "qwen2.5vl:7b"


def analyze_frame(frame_path: Path) -> str:
    """Describe visible UI evidence in one frame using local Ollama."""
    image_data = base64.b64encode(frame_path.read_bytes()).decode("ascii")

    payload = {
        "model": MODEL,
        "prompt": (
            "You are inspecting a screenshot from a silent software-testing "
            "recording. Describe only what is visibly supported by the image. "
            "Identify visible page titles, dialogs, error messages, disabled "
            "controls, and relevant UI state. Do not infer user intent, claim "
            "that something is a bug, or invent missing details. If text is "
            "unreadable, say so. Keep the observation concise."
        ),
        "images": [image_data],
        "stream": False,
    }

    request = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Local vision analysis failed: {error}") from error

    observation = result.get("response", "").strip()
    if not observation:
        raise RuntimeError("The vision model returned an empty observation.")

    return observation


def analyze_frames(frame_paths: list[Path], output_file: Path) -> list[dict]:
    """Analyze frames in order and save each observation as it completes."""
    observations = []

    output_file.parent.mkdir(parents=True, exist_ok=True)

    for index, frame_path in enumerate(frame_paths, start=1):
        # Extract the frame number for a useful timeline reference.
        try:
            frame_number = int(frame_path.stem.split("_")[-1])
            timestamp_seconds = (frame_number - 1) * 2
        except ValueError:
            frame_number = None
            timestamp_seconds = None

        print(f"[{index}/{len(frame_paths)}] Analyzing {frame_path.name}...")

        try:
            observation = analyze_frame(frame_path)
            result = {
                "frame": frame_path.name,
                "frame_number": frame_number,
                "timestamp_seconds": timestamp_seconds,
                "status": "success",
                "observation": observation,
            }
        except (RuntimeError, OSError) as error:
            result = {
                "frame": frame_path.name,
                "frame_number": frame_number,
                "timestamp_seconds": timestamp_seconds,
                "status": "failed",
                "error": str(error),
            }

        observations.append(result)

        # Save after every frame so completed work survives interruptions.
        with output_file.open("w", encoding="utf-8") as output:
            json.dump(observations, output, indent=2, ensure_ascii=False)
            output.write("\n")

        if result["status"] == "failed":
            print(f"  [WARNING] {result['error']}")
        else:
            print(f"  [OK] Observation saved.")

    print(f"\nSaved {len(observations)} observations to {output_file}")
    return observations
