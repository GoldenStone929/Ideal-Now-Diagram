# Getting Started

## Prerequisites

- Python 3.10+
- A virtual environment tool (venv, conda, etc.)

## Setup

1. Navigate to the project root:
   ```bash
   cd clinical-coding-center
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your API keys (if using LLM features).

## Orientation

1. Read `AGENTS.md` for the reading order.
2. Start with `knowledge/index.md` to understand the knowledge structure.
3. Browse `knowledge/scope/phase1_scope.md` to understand what Phase 1 covers.
4. Look at `tests/fixtures/` for example requests and assets.

## Running Tests

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `knowledge/` | Rules, policies, standards, schemas |
| `config/` | Runtime configuration |
| `data/` | Assets, registries, drafts, validated code |
| `workflows/` | High-level orchestration |
| `tools/` | Low-level utilities |
