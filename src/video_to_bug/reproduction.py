
import json
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_API = "http://localhost:11434"
MODEL = "qwen2.5vl:7b"
def review_proposal(observations: list[dict], proposal: dict) -> dict:
    """Ask the local model to review and correct a reproduction proposal."""
    prompt = f"""
You are an independent senior QA reviewer. Review the proposed bug report
against the original screenshot observations.

Your job is to correct reasoning errors, not merely improve the wording.

Check these issues carefully:
1. The primary reproduction steps must preserve the suspected triggering
   condition until the failure is reached.
2. Steps that remove or correct the suspected condition belong in suggested
   fixes or alternative tests, not in the primary reproduction steps.
3. Use the entire relevant timeline to reconstruct the setup and workflow.
4. An error message is evidence of what the application reports, even when
   the underlying configuration is not independently visible.
5. Keep observed actions distinct from inferred actions and unverified steps.
6. Expected behavior must be consistent with the evidence and any requirements
   explicitly stated by the application.
7. Suggested fixes must address the reported problem, not contradict it.
8. Do not invent application details or claim that the issue was reproduced.

Return a corrected report using exactly the same JSON structure and keys as
the proposal. Preserve useful evidence and exact error messages. If a claim
cannot be supported, qualify it or remove it. Do not add application-specific
rules. Return valid JSON only.

ORIGINAL OBSERVATIONS:
{json.dumps(observations, indent=2, ensure_ascii=False)}

PROPOSED REPORT:
{json.dumps(proposal, indent=2, ensure_ascii=False)}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "num_ctx": 16384,
            "temperature": 0.1,
        },
    }

    request = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
        reviewed = json.loads(result.get("response", ""))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Proposal review failed: {error}"
        ) from error

    return reviewed

def propose_reproduction(observations_file: Path, output_file: Path) -> dict:
    """Generate an evidence-based QA reproduction proposal using local Ollama."""
    observations = json.loads(
        observations_file.read_text(encoding="utf-8")
    )

    if not isinstance(observations, list):
        raise ValueError("Observations file must contain a JSON array.")

    successful = [
        item for item in observations
        if isinstance(item, dict) and item.get("status") == "success"
    ]

    if not successful:
        raise ValueError("No successful observations are available.")

    # Preserve chronological context instead of filtering for fixed keywords.
    evidence = [
        {
            "timestamp_seconds": item.get("timestamp_seconds"),
            "frame": item.get("frame"),
            "observation": item.get("observation", ""),
        }
        for item in successful
    ]

    prompt = f"""
You are an experienced QA engineer reconstructing a potential software issue
from timestamped screenshot observations extracted from a screen recording.

Your goal is to produce a useful, reproducible test scenario grounded in the
available evidence, not merely summarize the screenshots.

ANALYZE THE TIMELINE FIRST:
1. Read all observations in chronological order before drafting the report.
2. Identify the application's apparent workflow, important state changes,
   relevant controls, and the final error or unexpected result.
3. Connect earlier setup steps to later outcomes when the timeline supports
   that connection.
4. Distinguish a state visibly shown in a screenshot from an action inferred
   to have occurred between screenshots.
5. Give particular attention to explicit error messages. Treat their wording
   as evidence of what the application reports, even when the underlying
   configuration is not independently visible.
6. Do not ignore relevant context merely because it does not contain an
   error-related keyword.

EVIDENCE AND REASONING:
- Use only details supported by the observations or clearly labeled inferences.
- Preserve the exact wording of important error messages.
- An explicit error message can establish what the application reports about
  its state. Do not claim that the underlying state was independently verified
  unless the observations show it directly.
- Use timestamps and frame identifiers to support important claims.
- Do not infer that a particular click caused an error solely because the
  error appears in a later screenshot.
- Do not invent page names, controls, settings, actions, or application rules.
- If a necessary detail is missing, state what is unknown and propose a way
  to verify it.
- Keep the report specific to the actual evidence; do not use a generic
  reproduction template that ignores the recording's workflow.

REPRODUCTION STEPS:
- Construct the shortest practical sequence that preserves the suspected
  triggering conditions and reaches the observed result.
- Include relevant setup and configuration steps shown earlier in the
  recording, even if the error appears much later.
- Preserve suspected problematic conditions throughout the primary scenario.
  Do not resolve or remove the suspected cause before attempting the failure.
- Use visible controls and workflow stages from the observations when available.
- Do not present a troubleshooting action or proposed fix as a reproduction step.
- End the primary sequence with the action that plausibly triggers the result,
  followed by the result the tester should look for.
- If the precise triggering action is unknown, label it as inferred or
  unverified instead of inventing certainty.
- Do not claim that the proposed steps have been executed or that the issue
  has been independently reproduced.

Label each reproduction step:
- "observed": the action or state is directly supported by the evidence.
- "inferred": the action or condition is a plausible reconstruction from the
  timeline but is not directly shown.
- "unverified": the step depends on information that cannot be established
  from the observations.

EXPECTED RESULT:
- State a reasonable expected behavior when supported by the application
  workflow, visible interface, or error's explanation of valid alternatives.
- Explain the basis for that expectation.
- If the intended behavior genuinely cannot be determined, say so rather
  than inventing a requirement.
- Distinguish expected behavior from the observed result.

TROUBLESHOOTING AND ALTERNATIVE TESTS:
- Keep suggested fixes separate from reproduction steps.
- Tie each suggested fix to a specific suspected condition or failure.
- Treat fixes as proposals, not verified solutions.
- Suggest alternative tests only when they could meaningfully distinguish
  between plausible causes or verify an uncertain condition.
- Do not suggest modifying application source code.
- Do not add suggestions just to fill an array.

QUALITY CHECK BEFORE RESPONDING:
- Does the primary scenario preserve the suspected triggering conditions?
- Does it use the full relevant timeline rather than only the final screenshots?
- Does it include a plausible triggering action and the observed result?
- Does it distinguish application-reported facts from independently observed
  facts?
- Is the expected result justified?
- Are uncertain actions labeled honestly?
- Are troubleshooting suggestions separate from reproduction steps?
- Are important details specific to this recording rather than generic filler?

Return valid JSON only, with exactly these keys:

{{
  "title": "Concise, neutral issue title",
  "observed_result": "The result shown in the recording, preserving important error wording",
  "expected_result": "The expected behavior and its basis, or an explanation of what remains unknown",
  "reproduction_steps": [
    {{
      "step": "A specific action or setup condition",
      "evidence": "observed, inferred, or unverified",
      "basis": "Timestamped supporting evidence or explanation of uncertainty"
    }}
  ],
  "alternative_tests": [
    {{
      "test": "A distinct test to perform",
      "purpose": "What the test would help establish"
    }}
  ],
  "suggested_fixes": [
    {{
      "suggestion": "A potential fix or troubleshooting action",
      "rationale": "The condition it addresses and what remains unverified"
    }}
  ],
  "uncertainties": [
    "A specific remaining unknown or limitation"
  ]
}}

Use empty arrays when appropriate. Do not invent details to populate fields.

SCREENSHOT OBSERVATIONS:
{json.dumps(evidence, indent=2, ensure_ascii=False)}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "num_ctx": 16384,
            "temperature": 0.2,
        },
    }

    request = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Reproduction generation failed: {error}"
        ) from error

    raw_response = result.get("response", "")

    try:
        proposal = json.loads(raw_response)
    except json.JSONDecodeError as error:
        debug_file = output_file.with_suffix(".raw.txt")
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        debug_file.write_text(raw_response, encoding="utf-8")
        raise RuntimeError(
            f"The model returned invalid JSON. Raw response saved to: "
            f"{debug_file}"
        ) from error

    required_keys = {
        "title",
        "observed_result",
        "expected_result",
        "reproduction_steps",
        "alternative_tests",
        "suggested_fixes",
        "uncertainties",
    }

    if not isinstance(proposal, dict) or set(proposal) != required_keys:
        raise RuntimeError(
            "The model response does not contain exactly the required fields."
        )

    for key in (
        "title",
        "observed_result",
        "expected_result",
    ):
        if not isinstance(proposal[key], str) or not proposal[key].strip():
            raise RuntimeError(
                f"The model returned an empty or invalid '{key}' field."
            )

    for key in (
        "reproduction_steps",
        "alternative_tests",
        "suggested_fixes",
        "uncertainties",
    ):
        if not isinstance(proposal[key], list):
            raise RuntimeError(f"'{key}' must be a JSON array.")

    for index, step in enumerate(proposal["reproduction_steps"]):
        if not isinstance(step, dict):
            raise RuntimeError(
                f"Reproduction step {index + 1} must be a JSON object."
            )

        if not isinstance(step.get("step"), str) or not step["step"].strip():
            raise RuntimeError(
                f"Reproduction step {index + 1} is missing its action."
            )

        if step.get("evidence") not in {
            "observed",
            "inferred",
            "unverified",
        }:
            raise RuntimeError(
                f"Reproduction step {index + 1} has an invalid evidence label."
            )

        if not isinstance(step.get("basis"), str) or not step["basis"].strip():
            raise RuntimeError(
                f"Reproduction step {index + 1} is missing its evidence basis."
            )

    print("[INFO] Reviewing proposal for contradictions...")
    proposal = review_proposal(observations, proposal)

    if not isinstance(proposal, dict) or set(proposal) != required_keys:
        raise RuntimeError(
            "The reviewed proposal does not contain exactly the required fields."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(proposal, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Reproduction proposal saved to: {output_file}")
    return proposal
