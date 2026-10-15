
import json
from pathlib import Path


def generate_report(observations_file: Path, output_file: Path) -> None:
    """Create a readable Markdown report from saved frame observations."""
    observations = json.loads(
        observations_file.read_text(encoding="utf-8")
    )

    successful = [
        item for item in observations
        if item.get("status") == "success"
    ]
    failed = [
        item for item in observations
        if item.get("status") != "success"
    ]

    lines = [
        "# Screen Recording Analysis",
        "",
        "> Draft report generated from visual observations. "
        "Review before treating findings as confirmed bugs.",
        "",
        "## Timeline observations",
        "",
    ]

    if not successful:
        lines.append("No successful frame observations are available.")
    else:
        for item in successful:
            seconds = item.get("timestamp_seconds")
            timestamp = (
                f"{seconds // 60:02d}:{seconds % 60:02d}"
                if isinstance(seconds, (int, float))
                else "Unknown time"
            )

            lines.extend([
                f"### {timestamp} — {item.get('frame', 'Unknown frame')}",
                "",
                item.get("observation", "No observation text recorded."),
                "",
            ])

    lines.extend([
        "## Analysis limitations",
        "",
        "- These are model-generated descriptions of selected screenshots.",
        "- A screenshot alone may not establish what action caused a problem.",
        "- Reproduction steps and expected behavior have not been verified here.",
        f"- Frames successfully analyzed: {len(successful)}.",
        f"- Frames that failed analysis: {len(failed)}.",
        "",
    ])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Markdown report saved to: {output_file}")
