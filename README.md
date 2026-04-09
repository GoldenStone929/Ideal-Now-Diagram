# Clinical Coding Center

Local-first text-to-structure system for clinical coding workflows.

This project provides a web UI that converts long unstructured context (emails, SOPs, notes, stories, mixed logs) into:

- a dependency diagram with inspectable nodes/edges
- a structured "logic steps" explanation
- a folder-like section breakdown for traceability

It is designed to be robust under noisy inputs and still return a usable output via fallback logic when providers are unavailable.

---

## What It Does

1. Accepts long free-form text.
2. Chunks and normalizes the context.
3. Generates a structured outline (local model, external API, or fallback heuristics).
4. Infers sequential and cross-section dependencies.
5. Renders an interactive diagram and logic explanation.

---

## Key Features

- **Local Web UI** (single `serve.py`, no build pipeline).
- **Generation modes**:
  - Local LLM (Ollama-compatible endpoint)
  - External API (OpenAI-compatible endpoint)
- **Session API key input** in UI (no key hardcoded in source).
- **Progress bar + stage hints** during generation.
- **Failure classification** (invalid key, rate limit, timeout, server errors).
- **Dynamic edge overlap adjustment** to reduce line collisions.
- **Multi-spine layout** for complex contexts.
- **Color-coded edge types** (sequential, cross dependency, input, output, failure).
- **Structured Logic Steps panel** (auto-generated textual explanation).
- **PNG export** using the current browser viewport.
- **Automatic cache-busting/version refresh** in UI.

---

## Tech Stack

- Python `>=3.10`
- Standard library HTTP server (`http.server` + threading)
- `jsonschema`, `pydantic`, `pyyaml`, `rich`
- Frontend: vanilla HTML/CSS/JS (embedded in `serve.py`)

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

### 1) Create environment and install dependencies

```bash
cd clinical-coding-center
python -m venv .venv
```

Activate:

- Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

- macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

### 2) Prepare environment file

```bash
cp .env.example .env
```

If you are on Windows CMD:

```cmd
copy .env.example .env
```

### 3) Run the app

```bash
python serve.py
```

Default URL: `http://localhost:8118`

---

## API Key Configuration

You can set external API key in either way:

1. **UI session key (recommended for local testing)**  
   Use the `OpenAI API Key` input in the page and click `Set Key`.  
   This sets key in the current server session (not persisted automatically).

2. **`.env` file (persistent local config)**  
   Set:
   - `OPENAI_API_KEY=...`
   - `EXTERNAL_LLM_API_URL=...`
   - `EXTERNAL_LLM_MODEL=...`

> Security note: never commit real keys to Git.

---

## Usage

1. Paste long context into the main textarea.
2. Select generation mode (`local` or `external`).
3. Click `Send`.
4. Watch progress bar and stage messages.
5. Inspect:
   - diagram edges/nodes
   - connection details
   - structured logic steps panel
6. Export diagram as PNG if needed.

---

## Running Tests

Run full test suite:

```bash
python -m pytest -q
```

Run stress/robustness suites:

```bash
python -m pytest tests/integration/test_diagram_output_stress.py -q
python -m pytest tests/integration/test_diagram_ultimate_robustness.py -q
```

---

## HTTP Endpoints (Local Server)

- `GET /` - Web UI
- `GET /api/tree` - project tree
- `GET /api/file/<path>` - file viewer content
- `GET /api/version` - app version
- `GET /api/diagram/test-cases` - bundled generation cases
- `POST /api/diagram/generate` - main generation endpoint
- `GET /api/settings/openai-key-status` - external key configured status
- `POST /api/settings/openai-key` - set/clear external key for current session

---

## Troubleshooting

- **Generation timeout**: provider may be slow/stuck; retry or switch mode.
- **401/403**: invalid API key or no access; set key again.
- **429**: rate limit; wait and retry.
- **No diagram lines visible**: ensure input is non-empty and generation completed.
- **Unexpected layout overlap**: regenerate once; routing is dynamic per graph.

---

## Contributing

1. Create a feature branch.
2. Keep changes small and testable.
3. Run `python -m pytest -q` before PR.
4. Do not commit secrets (`.env`, keys).

---

## License

Add your preferred license file (for example `LICENSE`) before publishing publicly.
