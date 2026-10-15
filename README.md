# Video to Bug

A local-first command-line prototype that analyzes screen recordings of software testing sessions and generates timestamped observations and draft bug reports.

## Features

- Extracts frames from screen recordings using FFmpeg.
- Selects representative frames across the recording.
- Analyzes visible UI states with a locally hosted Ollama vision model.
- Generates a Markdown report with timestamps and analysis limitations.
- Keeps reproduction proposals separate from the initial screen-recording analysis.

## Requirements

- Python 3.9 or newer
- FFmpeg, including `ffprobe`
- [Ollama](https://ollama.com/)
- The local vision model `qwen2.5vl:7b` (or a compatible model configured in the source)

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/angelodeasis/video-to-bug.git
cd video-to-bug
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the package:

```bash
python -m pip install -e .
```

Install and start Ollama separately, then download the model:

```bash
ollama pull qwen2.5vl:7b
```

Check the environment:

```bash
video-to-bug doctor
```

## Usage

Display available commands:

```bash
video-to-bug --help
```

Analyze a recording:

```bash
video-to-bug analyze path/to/recording.mp4
```

The generated report is saved under `output/` in a run-specific directory.

## Reproduction proposals

The original standalone reproduction script reads `output/bug_report_draft.md` and writes `output/reproduction_proposal.md`:

```bash
python propose_reproduction.py
```

To use a newly generated report, copy it to the expected input path before running the script:

```bash
cp output/YOUR_RUN_DIRECTORY/report.md output/bug_report_draft.md
python propose_reproduction.py
```

Replace `YOUR_RUN_DIRECTORY` with the actual run directory name.

## Privacy

The application is designed for local processing with Ollama. Review the code and your local environment before using recordings containing sensitive information. Keep recordings, generated reports, and other sensitive artifacts out of public repositories.

## Project status

Early prototype. Outputs are drafts that require human review. Screenshot descriptions do not necessarily establish the exact actions that caused a bug, and proposed reproduction steps have not been independently verified.