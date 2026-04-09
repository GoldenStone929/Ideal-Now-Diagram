# Ideal-Now Diagram

Any-context text-to-logic diagram generator.

> Note: the very first prototype used a "Clinical Coding Center" architecture example.  
> The current product is **not clinical-only**. It starts with an empty canvas and generates structure from **whatever context the user pastes**.

This project provides a local web app where users can:

- paste any long context (emails, brainstorms, SOPs, stories, meeting notes, logs, product ideas, etc.)
- choose model mode (local LLM or external API)
- input their own API key in the UI (session-level)
- generate a structured dependency diagram + step-by-step logic text

---

## What It Does

1. Accepts raw free-form text from the input box.
2. Splits long context into chunks and normalizes it.
3. Builds a structured outline with major sections and key points.
4. Infers sequential and cross-section relationships.
5. Renders an interactive diagram plus a full "Structured Logic Steps" explanation.
6. Falls back to heuristic generation if providers are unavailable.

---

## Key Features

- **Empty-by-default canvas** (no fixed starter diagram/template).
- **Send-driven pipeline** (`Send` button or `Ctrl/Cmd + Enter`).
- **Model switch**:
  - Local LLM mode
  - External API mode (OpenAI-compatible, currently default in UI)
- **User API key input in UI** (`OpenAI API Key` + `Set Key`).
- **Progress bar with generation stages** and clear failure messages.
- **Color-coded edges** (`main`, `sequential`, `cross`, `input`, `output`, `fail`).
- **Dynamic edge offset/routing** to reduce overlap.
- **Adaptive layout** (single-spine / multi-spine for complex content).
- **Structured Logic Steps panel** auto-expanded to full content height.
- **Export Diagram** to PNG based on current viewport sizing.
- **Auto version refresh** to reduce stale frontend cache issues.

---

## Typical Inputs

- "Messy brainstorm with mixed priorities"
- "Customer email + internal action plan"
- "Long SOP with exceptions and escalation rules"
- "Narrative story that still has causal structure"

As long as there is logical signal in the text, the system attempts to structure it.

---

## Tech Stack

- Python `>=3.10`
- Local server: `http.server` + threaded mixin
- Core libs: `jsonschema`, `pydantic`, `pyyaml`, `rich`
- Frontend: vanilla HTML/CSS/JS embedded in `serve.py`

---

## Project Structure

```text
clinical-coding-center/
├── serve.py
├── diagram_autogen/
│   ├── __init__.py
│   └── pipeline.py
├── knowledge/
├── config/
├── data/
├── workflows/
├── tools/
├── prompts/
├── tests/
├── docs/
├── evals/
├── .env.example
├── requirements.txt
└── pyproject.toml
```

---

## Quick Start

### 1) Create environment and install

```bash
cd clinical-coding-center
python -m venv .venv
```

Activate:

- Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

- macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2) Create local env file

```bash
cp .env.example .env
```

Windows CMD:

```cmd
copy .env.example .env
```

### 3) Start server

```bash
python serve.py
```

Default URL: `http://localhost:8118`

---

## API Key Setup

Recommended flow for external API mode:

1. Open the web page.
2. Enter key in `OpenAI API Key`.
3. Click `Set Key`.
4. Switch to external mode and click `Send`.

The key is stored in current server session (not auto-persisted to Git files).

You may also set it in `.env`:

- `OPENAI_API_KEY=...`
- `EXTERNAL_LLM_API_URL=...`
- `EXTERNAL_LLM_MODEL=...`

Never commit real keys to the repository.

---

## Usage

1. Paste any text context into the main textarea.
2. Select local or external generation mode.
3. Click `Send`.
4. Track progress messages.
5. Inspect nodes/edges and their connection details.
6. Read generated "Structured Logic Steps".
7. Export PNG if needed.

---

## Tests

Run all tests:

```bash
python -m pytest -q
```

Run robustness suites:

```bash
python -m pytest tests/integration/test_diagram_output_stress.py -q
python -m pytest tests/integration/test_diagram_ultimate_robustness.py -q
```

---

## Local HTTP Endpoints

- `GET /` - web UI
- `GET /api/tree` - project tree data
- `GET /api/file/<path>` - file viewer content
- `GET /api/version` - version info for frontend refresh
- `GET /api/diagram/test-cases` - built-in generation test data
- `POST /api/diagram/generate` - text-to-diagram generation API
- `GET /api/settings/openai-key-status` - external key status
- `POST /api/settings/openai-key` - set/clear external key for current session

---

## Troubleshooting

- **Timeout**: provider is slow; retry or switch mode.
- **401/403**: key invalid or access denied; set key again.
- **429**: rate limit reached; wait and retry.
- **No output**: verify non-empty input and generation status.
- **Crowded lines**: regenerate once; edge routing adjusts per graph.

---

## Contributing

1. Create a branch.
2. Keep changes focused and testable.
3. Run `python -m pytest -q`.
4. Do not commit secrets (`.env`, API keys).

---

## License

Add your preferred license file (`LICENSE`) before public release.
