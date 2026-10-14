
from pathlib import Path
import re

INPUT = Path("output/failure_observations.md")
OUTPUT = Path("output/observation_summary.md")

# Higher scores indicate stronger evidence of a possible issue.
RULES = [
    # Critical: known validation failures
    (r"validation failed", 100),
    (r"sourcing mandate.{0,100}disabled", 90),
    (r"enabled.{0,100}disabled for every lot", 90),
    (r"disable it at the project level", 90),

    # Other validation evidence
    (r"validation error|failed validation", 12),
    (r"\binvalid\b|\bfails? validation\b", 7),
    (r"error message|error text|error displayed", 8),
    (r"red circle|red x|error icon", 6),
    (r"\bdisabled\b|cannot proceed|unable to proceed", 4),
    (r"\brequired\b|at least \d+|must be selected", 3),
    (r"\bwarning\b|\bpenalty\b", 2),
    (r"\bunchecked\b|\bchecked\b", 1),
]
def score_text(text):
    score = 0
    for pattern, points in RULES:
        if re.search(pattern, text, re.IGNORECASE):
            score += points
    return score

def extract_evidence(text):
    # Split the observation into short, readable pieces.
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text)
    ranked = []

    for piece in pieces:
        piece = piece.strip(" -*\t")
        if not piece:
            continue

        score = score_text(piece)
        if score >= 2:
            ranked.append((score, piece))

    # Keep the strongest evidence, preserving exact wording.
    ranked.sort(key=lambda item: item[0], reverse=True)

    selected = []
    seen = set()

    for _, piece in ranked:
        if piece not in seen:
            selected.append(piece)
            seen.add(piece)
        if len(selected) == 4:
            break

    return selected

def main():
    if not INPUT.exists():
        print(f"Report not found: {INPUT}")
        return

    report = INPUT.read_text(encoding="utf-8")
    sections = re.split(
        r"(?=^## frame_\d+\.jpg)",
        report,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    candidates = []

    for section in sections:
        section = section.strip()
        if not section.startswith("## frame_"):
            continue

        lines = section.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        score = score_text(body)
        evidence = extract_evidence(body)

        if score > 0 and evidence:
            candidates.append({
                "heading": heading,
                "score": score,
                "evidence": evidence,
            })

    # Highest-priority frames first, capped at 15.
    candidates.sort(key=lambda item: item["score"], reverse=True)
    selected = candidates[:15]

    output = [
        "# Prioritized Observation Summary",
        "",
        f"Source: `{INPUT}`",
        f"Frames analyzed: {len(sections) - 1}",
        f"Frames with prioritized evidence: {len(candidates)}",
        f"Frames included below: {len(selected)}",
        "",
        "> These are candidate signals, not confirmed bugs. "
        "The score is a keyword-based priority, not a confidence level.",
        "",
    ]

    for item in selected:
        output.append(f"## {item['heading']}")
        output.append(f"Priority score: {item['score']}")
        output.append("")

        for sentence in item["evidence"]:
            output.append(f"- {sentence}")

        output.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(output), encoding="utf-8")

    print(f"Saved: {OUTPUT}")
    print(f"Frames with evidence: {len(candidates)}")
    print(f"Frames included: {len(selected)}")

if __name__ == "__main__":
    main()
