
from pathlib import Path
import base64
import json
import urllib.request
import urllib.error

MODEL = "qwen2.5vl:7b"
FRAME_DIR = Path("output/frames")
FRAME_NUMBERS = range(41, 45)

PROMPT = """
You are analyzing a screen recording to help reconstruct software
bug reproduction steps. Analyze this single screenshot only.

Return:
1. Visible page or UI state.
2. Visible labels, buttons, checkboxes, and their apparent states.
3. Any visible error message, transcribed exactly when readable.
4. What appears different from a normal usable form, if anything.
5. What cannot be determined from this screenshot.

Do not invent clicks, user actions, causes, or text you cannot read.
Do not diagnose the bug. Describe evidence only.
"""

def analyze_frame(path: Path) -> str:
    image_data = base64.b64encode(path.read_bytes()).decode("ascii")

    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "images": [image_data],
        "stream": False,
    }

    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"]


def main():
    output_path = Path("output/failure_observations_41_44.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as report:
        for number in FRAME_NUMBERS:
            frame = FRAME_DIR / f"frame_{number:04d}.jpg"

            if not frame.exists():
                print(f"Missing: {frame}")
                continue

            timestamp = (number - 1) * 2
            print(f"Analyzing {frame.name} (~{timestamp}s)...")

            try:
                observation = analyze_frame(frame)
            except (urllib.error.URLError, TimeoutError) as error:
                observation = f"Analysis failed: {error}"

            report.write(
                f"## {frame.name} — approximately {timestamp}s\n\n"
                f"{observation}\n\n"
                "---\n\n"
            )
            report.flush()

    print(f"Saved observations to {output_path}")


if __name__ == "__main__":
    main()
