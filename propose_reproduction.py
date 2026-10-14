
from pathlib import Path
import json
import urllib.request

MODEL = "qwen2.5vl:7b"

REPORT_PATH = Path("output/bug_report_draft.md")
OUTPUT_PATH = Path("output/reproduction_proposal.md")

if not REPORT_PATH.exists():
    raise SystemExit(f"Report not found: {REPORT_PATH}")

report = REPORT_PATH.read_text(encoding="utf-8")

prompt = f"""
You are a QA engineer reviewing evidence from a silent screen recording.

Your task is to propose a practical way to reproduce the reported error,
using only the evidence in the report below.

IMPORTANT RULES:
- Do not claim that proposed actions were definitely performed by the tester.
- Separate observed facts, reasonable inferences, and unverified guesses.
- Do not invent exact clicks, field values, or configuration settings.
- Identify the minimum setup and actions that should be tested.
- Explain how to confirm whether each attempt reproduced the error.
- If multiple explanations are possible, propose separate test cases.
- Preserve the exact validation error message.
- Do not suggest changing application code or fixing the error.
- The goal is to reproduce the error, not diagnose or repair it.

Return these sections:
1. Error to reproduce
2. Facts established by the evidence
3. Proposed reproduction steps
4. Alternative test cases
5. Expected observable result
6. Unknowns to verify
7. Confidence and limitations

For each proposed step, label it OBSERVED, INFERRED, or UNVERIFIED.

REPORT:
--- BEGIN REPORT ---
{report}
--- END REPORT ---
"""

payload = json.dumps({
    "model": MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.2
    }
}).encode("utf-8")

request = urllib.request.Request(
    "http://localhost:11434/api/generate",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print(f"Sending report to local model: {MODEL}")

try:
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))
except Exception as exc:
    raise SystemExit(
        f"Model request failed: {exc}\n"
        "Check that Ollama is running and the model is installed."
    )

proposal = result.get("response", "").strip()

if not proposal:
    raise SystemExit("The model returned an empty proposal.")

OUTPUT_PATH.write_text(proposal + "\n", encoding="utf-8")

print(f"Proposal saved to: {OUTPUT_PATH}")
print(f"Characters generated: {len(proposal)}")
