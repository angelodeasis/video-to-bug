
from pathlib import Path
import re

OUTPUT_DIR = Path("output")

SOURCE_FILES = [
    OUTPUT_DIR / "observations_frames_41_44.md",
    OUTPUT_DIR / "failure_observations_backup.md",
]

REPORT_FILE = OUTPUT_DIR / "bug_report_draft.md"


def load_observations():
    observations = {}

    for path in SOURCE_FILES:
        if not path.exists():
            print(f"Warning: missing observation file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        sections = re.split(r"(?=^## frame_\d+\.jpg)", content, flags=re.MULTILINE)

        for section in sections:
            match = re.match(
                r"^## (frame_(\d+)\.jpg).*?(?:\n|$)",
                section,
            )
            if not match:
                continue

            filename = match.group(1)
            frame_number = int(match.group(2))

            # Prefer the first saved observation if a frame appears twice.
            observations.setdefault(frame_number, {
                "filename": filename,
                "notes": section.strip(),
            })

    return observations


def build_report(observations):
    lines = [
        "# Draft Bug Report",
        "",
        "> Status: Preliminary — human review required.",
        "> Generated from local video-frame observations. No automated "
        "claim about the root cause is made.",
        "",
        "## Summary",
        "",
        "A validation message appears in the recorded workflow and prevents "
        "the user from proceeding with the Next button.",
        "",
        "## Observed result",
        "",
        'The application displays: "Validation Failed: Sourcing Mandate is '
        'enabled for the project but disabled for every lot. Please disable '
        'it at the project level or enable it for at least one lot."',
        "",
        "The Next button appears disabled when this message is visible.",
        "",
        "## Expected result",
        "",
        "Not established from the recording alone. Confirm the intended "
        "project-level and lot-level configuration with the application "
        "requirements or a product owner.",
        "",
        "## Timeline and evidence",
        "",
    ]

    for number in sorted(observations):
        item = observations[number]
        timestamp = (number - 1) * 2

        lines.extend([
            f"### Frame {number} — approximately {timestamp}s",
            "",
            f"![Evidence from {item['filename']}](frames/{item['filename']})",
            "",
            item["notes"],
            "",
        ])

    lines.extend([
        "## Preliminary interpretation",
        "",
        "- Around 86s, a prompt asks whether to export values to the Price Matrix.",
        "- Around 88s, Sourcing Mandate appears checked in the Price Matrix section.",
        "- Around 98s, the project-versus-lot validation message is visible.",
        "- These events occur in sequence, but the available screenshots do not "
        "prove that exporting values caused the validation error.",
        "",
        "## Unknowns and follow-up",
        "",
        "- Which exact user action first triggers the validation message?",
        "- Does the visible Sourcing Mandate checkbox control the project or a lot?",
        "- What project and lot settings are expected for this workflow?",
        "- Can the issue be reproduced consistently from a known starting state?",
        "",
        "## Reproduction steps",
        "",
        "Not yet confirmed. The recording shows part of the workflow, but the "
        "exact actions and initial configuration still need verification.",
        "",
        "## Confidence",
        "",
        "- **High confidence:** the validation message is visible in the saved "
        "observation for frame 50.",
        "- **Moderate confidence:** the preceding frames show the overhead, "
        "bonus/penalty, and Price Matrix workflow.",
        "- **Low confidence:** any claim that a particular action or checkbox "
        "caused the error.",
        "",
        "---",
        "",
        "This is an evidence draft, not a confirmed diagnosis. Review the "
        "screenshots and replace approximate timestamps with exact timings "
        "if needed.",
    ])

    return "\n".join(lines) + "\n"


def main():
    observations = load_observations()

    if not observations:
        raise SystemExit(
            "No frame observations found. Check the source filenames."
        )

    REPORT_FILE.write_text(
        build_report(observations),
        encoding="utf-8",
    )

    print(f"Frames included: {len(observations)}")
    print(f"Report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
