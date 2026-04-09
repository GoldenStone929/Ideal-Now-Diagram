"""Ideal-Now Diagram - Local Web UI (offline, no CDN)."""

from __future__ import annotations

import json
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


def _load_env_file(env_path: Path) -> None:
    """Load KEY=VALUE pairs from .env if present."""
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        parsed = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, parsed)


_load_env_file(ROOT / ".env")

from diagram_autogen import generate_diagram_payload, get_generation_test_cases

SELF_FILE = Path(__file__).resolve()
PORT = 8118
MAX_FILE_SIZE = 2_000_000
MAX_GENERATE_INPUT_SIZE = 180_000
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
ALLOWED_DOT_FILES = {".env.example", ".gitignore"}
APP_VERSION = f"{int(SELF_FILE.stat().st_mtime)}-{SELF_FILE.stat().st_size}"


def _safe_path(rel_path: str) -> Path | None:
    """Resolve rel_path under ROOT, blocking traversal."""
    try:
        candidate = (ROOT / rel_path).resolve()
    except (OSError, RuntimeError):
        return None
    if candidate == ROOT or ROOT in candidate.parents:
        return candidate
    return None


def build_tree(base: Path, rel: Path | None = None) -> list[dict]:
    target = base if rel is None else base / rel
    entries: list[dict] = []
    try:
        children = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return entries

    for child in children:
        if child.name.startswith(".") and child.name not in ALLOWED_DOT_FILES:
            continue
        if child.name in SKIP_DIRS:
            continue

        relative = child.relative_to(base).as_posix()
        if child.is_dir():
            entries.append(
                {
                    "name": child.name,
                    "path": relative,
                    "type": "dir",
                    "children": build_tree(base, child.relative_to(base)),
                }
            )
        else:
            entries.append(
                {
                    "name": child.name,
                    "path": relative,
                    "type": "file",
                    "ext": child.suffix.lstrip(".").lower(),
                }
            )
    return entries


def read_file_content(rel_path: str) -> tuple[str, str]:
    file_path = _safe_path(rel_path)
    if file_path is None or not file_path.exists() or not file_path.is_file():
        return "File not found.", "text"
    if file_path.stat().st_size > MAX_FILE_SIZE:
        return "File too large to display.", "text"

    ext = file_path.suffix.lstrip(".").lower()
    lang_map = {
        "py": "python",
        "md": "markdown",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "toml": "toml",
        "sas": "sas",
        "r": "r",
        "sql": "sql",
        "txt": "text",
        "sh": "bash",
        "ps1": "powershell",
        "vbs": "vbscript",
    }
    lang = lang_map.get(ext, "text")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding="latin-1")
        except Exception as exc:  # pragma: no cover - defensive
            return f"Cannot read file: {exc}", "text"
    except Exception as exc:  # pragma: no cover - defensive
        return f"Cannot read file: {exc}", "text"
    return content, lang


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _set_no_cache_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-App-Version", APP_VERSION)

    def _json(self, data: dict | list, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_no_cache_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length_raw = self.headers.get("Content-Length", "0")
        try:
            content_length = int(length_raw)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header.") from exc
        if content_length <= 0:
            raise ValueError("Request body is empty.")
        if content_length > MAX_GENERATE_INPUT_SIZE:
            raise ValueError(f"Input too large. Limit is {MAX_GENERATE_INPUT_SIZE} bytes.")
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body is not valid JSON.") from exc
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def do_GET(self):
        parsed = urlsplit(unquote(self.path))
        path = parsed.path
        if path in ("/", "/index.html"):
            html = INDEX_HTML.replace("__APP_VERSION__", APP_VERSION).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self._set_no_cache_headers()
            self.end_headers()
            self.wfile.write(html)
            return

        if path == "/api/tree":
            self._json(build_tree(ROOT))
            return

        if path == "/api/version":
            self._json({"version": APP_VERSION})
            return

        if path == "/api/settings/openai-key-status":
            configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
            self._json({"configured": configured})
            return

        if path == "/api/diagram/test-cases":
            self._json({"cases": get_generation_test_cases()})
            return

        if path.startswith("/api/file/"):
            rel = path[len("/api/file/") :]
            content, lang = read_file_content(rel)
            self._json({"path": rel, "language": lang, "content": content})
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlsplit(unquote(self.path))
        path = parsed.path

        if path == "/api/settings/openai-key":
            try:
                payload = self._read_json_body()
            except ValueError as exc:
                self._json({"error": str(exc)}, status=400)
                return

            key = str(payload.get("openai_api_key", "")).strip()
            if len(key) > 4096:
                self._json({"error": "API key is too long."}, status=400)
                return
            os.environ["OPENAI_API_KEY"] = key
            self._json({"ok": True, "configured": bool(key)})
            return

        if path == "/api/diagram/generate":
            try:
                payload = self._read_json_body()
            except ValueError as exc:
                self._json({"error": str(exc)}, status=400)
                return

            mode = str(payload.get("mode", "local")).strip().lower()
            mode = "external" if mode == "external" else "local"
            text = str(payload.get("text", ""))
            allow_llm = bool(payload.get("allow_llm", True))
            llm_attempts = int(payload.get("llm_attempts", 2))
            llm_attempts = max(0, min(4, llm_attempts))

            try:
                result = generate_diagram_payload(
                    text=text,
                    mode=mode,
                    allow_llm=allow_llm,
                    llm_attempts=llm_attempts,
                )
            except ValueError as exc:
                self._json({"error": str(exc)}, status=400)
                return
            except Exception as exc:  # pragma: no cover - defensive
                self._json({"error": f"Generation failed: {exc}"}, status=500)
                return

            self._json(result)
            return

        self.send_error(404)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Ideal-Now Diagram</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; font-family: "Segoe UI", system-ui, sans-serif; background: #0d1117; color: #e6edf3; }
    #app { display: flex; height: 100vh; overflow: hidden; }
    #sidebar { width: 310px; flex-shrink: 0; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; }
    #sidebar-head { padding: 14px; border-bottom: 1px solid #30363d; }
    #sidebar-head h1 { font-size: 12px; letter-spacing: .6px; text-transform: uppercase; color: #8b949e; margin-bottom: 8px; }
    #search { width: 100%; height: 34px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #e6edf3; padding: 0 10px; }
    #search:focus { outline: none; border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88,166,255,.15); }
    #tree-wrap { flex: 1; min-height: 180px; overflow: auto; padding: 8px 0; }
    #resize-handle { width: 5px; cursor: col-resize; background: transparent; flex-shrink: 0; }
    #resize-handle:hover { background: #58a6ff; }
    #app.sidebar-hidden #sidebar, #app.sidebar-hidden #resize-handle { display: none; }
    #app.sidebar-hidden #main { width: 100%; }
    .tree-item { height: 28px; display: flex; align-items: center; gap: 8px; margin: 1px 8px; border-radius: 6px; color: #c9d1d9; cursor: pointer; font-size: 13px; }
    .tree-item:hover { background: #1c2128; }
    .tree-item.active { background: #1c2d40; color: #58a6ff; font-weight: 600; }
    .tree-item .icon { width: 16px; text-align: center; color: #8b949e; }
    .tree-item.hidden { display: none; }
    .tree-children.collapsed { display: none; }
    .tree-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    #main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
    #topbar { height: 44px; border-bottom: 1px solid #30363d; background: #161b22; display: flex; align-items: center; gap: 8px; padding: 0 14px; }
    .tab-btn { height: 30px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #8b949e; padding: 0 10px; cursor: pointer; font-size: 12px; }
    .tab-btn.active { border-color: #58a6ff; color: #58a6ff; background: #132337; }
    .tab-btn:disabled { opacity: .55; cursor: not-allowed; }
    #status { margin-left: auto; color: #8b949e; font-size: 12px; }
    #app-version { color: #58a6ff; font-size: 11px; border: 1px solid #30363d; border-radius: 12px; padding: 2px 8px; background: #0d1117; }
    .view { display: none; height: calc(100vh - 44px); }
    .view.active { display: block; }
    #diagram-view { padding: 16px; overflow: auto; }
    #diagram-builder { margin-bottom: 14px; border: 1px solid #30363d; border-radius: 10px; background: #161b22; padding: 12px; }
    #builder-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
    #builder-head label { color: #8b949e; font-size: 12px; }
    #llm-mode { height: 30px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #e6edf3; padding: 0 10px; font-size: 12px; }
    #api-key-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
    #api-key-row label { color: #8b949e; font-size: 12px; }
    #api-key-input { height: 30px; min-width: 280px; flex: 1 1 340px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #e6edf3; padding: 0 10px; font-size: 12px; }
    #api-key-input:focus { outline: none; border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88,166,255,.14); }
    #save-api-key { height: 30px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #8b949e; padding: 0 12px; cursor: pointer; font-size: 12px; }
    #save-api-key:hover { border-color: #58a6ff; color: #58a6ff; }
    #save-api-key:disabled { opacity: .6; cursor: not-allowed; }
    #api-key-status { color: #8b949e; font-size: 12px; white-space: nowrap; }
    #send-row { display: flex; justify-content: flex-end; margin-top: 10px; }
    #generate-diagram { height: 34px; min-width: 96px; border: 1px solid #e25b5b; border-radius: 6px; background: #b42324; color: #ffffff; padding: 0 14px; cursor: pointer; font-size: 12px; font-weight: 600; }
    #generate-diagram:hover { background: #cc2f2f; border-color: #ff7b7b; }
    #generate-diagram:disabled { opacity: .62; cursor: not-allowed; background: #7e1c1d; border-color: #944142; color: #f8d7da; }
    #context-input { width: 100%; min-height: 130px; resize: vertical; border: 1px solid #30363d; border-radius: 8px; background: #0d1117; color: #e6edf3; padding: 10px; line-height: 1.45; font-size: 13px; }
    #context-input:focus { outline: none; border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88,166,255,.14); }
    #builder-note { color: #8b949e; font-size: 12px; margin-top: 8px; line-height: 1.45; }
    #gen-progress-wrap { margin-top: 10px; }
    #gen-progress-track { width: 100%; height: 10px; border-radius: 999px; border: 1px solid #30363d; background: #0d1117; overflow: hidden; }
    #gen-progress-bar { height: 100%; width: 0%; background: linear-gradient(90deg, #3b82f6 0%, #58a6ff 100%); transition: width .35s ease; }
    #gen-progress-bar.running { background-size: 180% 100%; animation: gen-progress-shimmer 1.2s linear infinite; }
    #gen-progress-bar.success { background: linear-gradient(90deg, #2ea043 0%, #3fb950 100%); }
    #gen-progress-bar.error { background: linear-gradient(90deg, #d73a49 0%, #f85149 100%); }
    #gen-progress-text { margin-top: 6px; color: #8b949e; font-size: 12px; line-height: 1.4; min-height: 16px; }
    @keyframes gen-progress-shimmer {
      from { background-position: 0% 0%; }
      to { background-position: 180% 0%; }
    }
    #logic-steps-wrap { margin-top: 14px; border: 1px solid #30363d; border-radius: 10px; background: #161b22; padding: 12px; }
    #logic-steps-head { color: #8b949e; font-size: 12px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .4px; }
    #logic-steps-output { width: 100%; min-height: 210px; resize: none; overflow: hidden; border: 1px solid #30363d; border-radius: 8px; background: #0d1117; color: #c9d1d9; padding: 10px; line-height: 1.45; font-size: 12.5px; font-family: Consolas, "Cascadia Code", monospace; }
    #logic-steps-output:focus { outline: none; border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88,166,255,.14); }
    #diagram-grid { display: grid; grid-template-columns: minmax(860px, 1fr) 380px; gap: 14px; align-items: start; }
    #diagram-canvas { background: #0f141b; border: 1px solid #30363d; border-radius: 10px; padding: 12px; overflow: auto; }
    #diagram-svg { width: 100%; max-width: 1150px; min-height: 900px; display: block; margin: 0 auto; }
    #diagram-right { display: flex; flex-direction: column; gap: 14px; position: sticky; top: 0; }
    #inspector, #block-inspector { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 14px; }
    #block-inspector { min-height: 240px; }
    #block-inspector-body ul { margin-left: 18px; color: #c9d1d9; font-size: 12.8px; line-height: 1.5; }
    #inspector h2 { font-size: 16px; margin-bottom: 10px; }
    .hint { color: #8b949e; font-size: 13px; line-height: 1.5; margin-bottom: 8px; }
    .mini-btn { height: 28px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #8b949e; padding: 0 10px; cursor: pointer; font-size: 12px; }
    .mini-btn:hover { border-color: #58a6ff; color: #58a6ff; }
    .hidden-tech { display: none; }
    .k { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: .4px; margin-top: 10px; margin-bottom: 4px; }
    .v { color: #e6edf3; font-size: 13px; line-height: 1.5; }
    #file-view { padding: 16px; overflow: auto; }
    #file-meta { height: 36px; border: 1px solid #30363d; border-radius: 8px; display: flex; align-items: center; padding: 0 12px; color: #8b949e; font-size: 12px; margin-bottom: 10px; background: #161b22; }
    #file-content { white-space: pre-wrap; word-break: break-word; background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 16px; font-size: 13px; line-height: 1.55; color: #c9d1d9; font-family: Consolas, "Cascadia Code", monospace; }
    .edge-visible { fill: none; stroke-width: 2.1; }
    .edge-hit { fill: none; stroke: transparent; stroke-width: 14; cursor: pointer; }
    .edge-selected { stroke: #ffcc66 !important; stroke-width: 3.2 !important; }
    .node-box { cursor: pointer; }
    .node-box.selected rect { stroke: #ffcc66 !important; stroke-width: 2.8 !important; }
    .legend { font-size: 11px; fill: #8b949e; }
  </style>
</head>
<body>
  <div id="app" class="sidebar-hidden">
    <aside id="sidebar">
      <div id="sidebar-head">
        <h1>Ideal-Now Diagram</h1>
        <input id="search" placeholder="Search files..." />
      </div>
      <div id="tree-wrap"></div>
    </aside>
    <div id="resize-handle"></div>
    <main id="main">
      <div id="topbar">
        <button id="toggle-explorer" class="tab-btn">Show Explorer</button>
        <button id="tab-diagram" class="tab-btn active">Diagram</button>
        <button id="tab-file" class="tab-btn">File Viewer</button>
        <button id="export-diagram" class="tab-btn">Export Diagram</button>
        <span id="status">Click a block for Block Main Details, or click an arrow for connection reasons.</span>
        <span id="app-version">v__APP_VERSION__</span>
      </div>

      <section id="diagram-view" class="view active">
        <div id="diagram-builder">
          <div id="builder-head">
            <label for="llm-mode">Generation mode</label>
            <select id="llm-mode">
              <option value="local">Local LLM</option>
              <option value="external" selected>External API (default)</option>
            </select>
          </div>
          <div id="api-key-row">
            <label for="api-key-input">OpenAI API Key</label>
            <input id="api-key-input" type="password" placeholder="Paste API key (session only)..." autocomplete="off" />
            <button id="save-api-key" type="button">Set Key</button>
            <span id="api-key-status">Not set</span>
          </div>
          <textarea id="context-input" placeholder="Paste any long email, SOP, random notes, or even a story. The system will chunk it, structure it, and generate a section dependency diagram."></textarea>
          <div id="builder-note">Tool starts empty. Paste any context, then click Send (or Ctrl/Cmd + Enter). The pipeline runs chunking, structuring, dependency linking, validation, and fallback if needed.</div>
          <div id="gen-progress-wrap">
            <div id="gen-progress-track"><div id="gen-progress-bar"></div></div>
            <div id="gen-progress-text">Ready.</div>
          </div>
          <div id="send-row">
            <button id="generate-diagram">Send</button>
          </div>
        </div>
        <div id="diagram-grid">
          <div id="diagram-canvas"><svg id="diagram-svg" viewBox="0 0 1150 900"></svg></div>
          <div id="diagram-right">
            <aside id="inspector">
              <h2 id="inspector-title">Connection Details</h2>
              <div class="hint">Click any arrow to view: why connected and what it does.</div>
              <button id="toggle-tech" class="mini-btn">Show technical details</button>
              <div class="k">Selection</div>
              <div id="inspector-body" class="v">No selection yet.</div>
            </aside>
            <aside id="block-inspector">
              <h2 id="block-inspector-title">Block Main Details</h2>
              <div class="hint">Click any section box in the diagram.</div>
              <div id="block-inspector-body" class="v">No block selected yet.</div>
            </aside>
          </div>
        </div>
        <div id="logic-steps-wrap">
          <div id="logic-steps-head">Structured Logic Steps</div>
          <textarea id="logic-steps-output" readonly placeholder="Empty for now. After you click Send, the system will generate full step-by-step logic text here."></textarea>
        </div>
      </section>

      <section id="file-view" class="view">
        <div id="file-meta">Select a file from the left tree.</div>
        <pre id="file-content"></pre>
      </section>
    </main>
  </div>

  <script>
    (function () {
      const $ = (id) => document.getElementById(id);
      const app = $("app");
      const treeWrap = $("tree-wrap");
      const searchBox = $("search");
      const toggleExplorerBtn = $("toggle-explorer");
      const blockInspectorTitle = $("block-inspector-title");
      const blockInspectorBody = $("block-inspector-body");
      const tabDiagram = $("tab-diagram");
      const tabFile = $("tab-file");
      const exportDiagramBtn = $("export-diagram");
      const modeSelect = $("llm-mode");
      const apiKeyInput = $("api-key-input");
      const saveApiKeyBtn = $("save-api-key");
      const apiKeyStatus = $("api-key-status");
      const generateDiagramBtn = $("generate-diagram");
      const contextInput = $("context-input");
      const builderNote = $("builder-note");
      const logicStepsOutput = $("logic-steps-output");
      const progressBar = $("gen-progress-bar");
      const progressText = $("gen-progress-text");
      const statusEl = $("status");
      const versionEl = $("app-version");
      const diagramView = $("diagram-view");
      const fileView = $("file-view");
      const fileMeta = $("file-meta");
      const fileContent = $("file-content");
      const inspectorTitle = $("inspector-title");
      const inspectorBody = $("inspector-body");
      const toggleTechBtn = $("toggle-tech");
      const svg = $("diagram-svg");

      const NODE_W = 168;
      const NODE_H = 44;
      const HALF_W = NODE_W / 2;
      const HALF_H = NODE_H / 2;
      let showTechDetails = false;
      let sidebarVisible = false;
      let treeLoaded = false;
      const APP_VERSION = "__APP_VERSION__";
      const GENERATION_TIMEOUT_MS = 90000;
      let progressTicker = null;
      let progressStageTicker = null;
      let progressValue = 0;
      let externalApiKeyConfigured = false;

      const styles = {
        main: { fill: "#1c2d40", stroke: "#58a6ff", text: "#e6edf3", edge: "#58a6ff" },
        sequential: { fill: "#1c2d40", stroke: "#4ea1ff", text: "#e6edf3", edge: "#4ea1ff" },
        cross: { fill: "#221735", stroke: "#a371f7", text: "#d2a8ff", edge: "#a371f7" },
        input: { fill: "#122117", stroke: "#3fb950", text: "#7ee787", edge: "#3fb950" },
        output: { fill: "#1d1b0e", stroke: "#d29922", text: "#e3b341", edge: "#d29922" },
        fail: { fill: "#2d1616", stroke: "#f85149", text: "#ffa198", edge: "#f85149" },
      };
      let nodes = [];
      let edges = [];

      function createSvgEl(tag, attrs) {
        const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
        Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, String(v)));
        return el;
      }

      function setView(view) {
        const isDiagram = view === "diagram";
        diagramView.classList.toggle("active", isDiagram);
        fileView.classList.toggle("active", !isDiagram);
        tabDiagram.classList.toggle("active", isDiagram);
        tabFile.classList.toggle("active", !isDiagram);
        exportDiagramBtn.disabled = !isDiagram || nodes.length === 0;
      }

      function exportFileTimestamp() {
        const d = new Date();
        const pad = (n) => String(n).padStart(2, "0");
        return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
      }

      function attachExportSvgStyles(clonedSvg) {
        let defs = clonedSvg.querySelector("defs");
        if (!defs) {
          defs = createSvgEl("defs", {});
          clonedSvg.insertBefore(defs, clonedSvg.firstChild);
        }
        const styleEl = createSvgEl("style", {});
        styleEl.textContent = [
          ".edge-visible{fill:none;stroke-width:2.1;}",
          ".edge-hit{fill:none;stroke:transparent;stroke-width:14;}",
          ".edge-selected{stroke:#ffcc66;stroke-width:3.2;}",
          ".node-box.selected rect{stroke:#ffcc66;stroke-width:2.8;}",
          ".legend{font-size:11px;fill:#8b949e;font-family:'Segoe UI',system-ui,sans-serif;}",
          "text{font-family:'Segoe UI',system-ui,sans-serif;}",
        ].join("");
        defs.appendChild(styleEl);
      }

      async function exportDiagramPng() {
        const labelBefore = exportDiagramBtn.textContent;
        exportDiagramBtn.disabled = true;
        exportDiagramBtn.textContent = "Exporting...";
        try {
          const rect = svg.getBoundingClientRect();
          const width = Math.max(1, Math.round(rect.width));
          const height = Math.max(1, Math.round(rect.height));

          const clonedSvg = svg.cloneNode(true);
          clonedSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
          clonedSvg.setAttribute("width", String(width));
          clonedSvg.setAttribute("height", String(height));
          if (!clonedSvg.getAttribute("viewBox")) {
            clonedSvg.setAttribute("viewBox", `0 0 ${width} ${height}`);
          }
          attachExportSvgStyles(clonedSvg);

          const serialized = new XMLSerializer().serializeToString(clonedSvg);
          const svgBlob = new Blob([serialized], { type: "image/svg+xml;charset=utf-8" });
          const svgUrl = URL.createObjectURL(svgBlob);

          try {
            const img = await new Promise((resolve, reject) => {
              const temp = new Image();
              temp.onload = () => resolve(temp);
              temp.onerror = () => reject(new Error("Failed to render SVG for export."));
              temp.src = svgUrl;
            });

            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext("2d");
            if (!ctx) throw new Error("Canvas context unavailable.");
            ctx.fillStyle = "#0f141b";
            ctx.fillRect(0, 0, width, height);
            ctx.drawImage(img, 0, 0, width, height);

            const pngBlob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
            if (!pngBlob) throw new Error("Failed to create PNG file.");

            const filename = `ideal-now-diagram-${exportFileTimestamp()}-${width}x${height}.png`;
            const downloadUrl = URL.createObjectURL(pngBlob);
            const a = document.createElement("a");
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(downloadUrl);
            statusEl.textContent = `Diagram exported (${width}x${height}).`;
          } finally {
            URL.revokeObjectURL(svgUrl);
          }
        } catch (err) {
          statusEl.textContent = `Export failed: ${err && err.message ? err.message : "unknown error"}`;
        } finally {
          exportDiagramBtn.textContent = labelBefore;
          exportDiagramBtn.disabled = !diagramView.classList.contains("active") || nodes.length === 0;
        }
      }

      function anchorPoint(node, targetX, targetY) {
        const dx = targetX - node.x;
        const dy = targetY - node.y;
        if (dx === 0 && dy === 0) return [node.x, node.y];

        if (Math.abs(dx) * HALF_H > Math.abs(dy) * HALF_W) {
          const sx = dx > 0 ? 1 : -1;
          const y = node.y + (dy * HALF_W) / Math.abs(dx);
          return [node.x + sx * HALF_W, y];
        }
        const sy = dy > 0 ? 1 : -1;
        const x = node.x + (dx * HALF_H) / Math.abs(dy);
        return [x, node.y + sy * HALF_H];
      }

      function edgePoints(edge) {
        const from = nodeMap[edge.from];
        const to = nodeMap[edge.to];
        const via = edge.via || [];
        const first = via.length ? via[0] : [to.x, to.y];
        const last = via.length ? via[via.length - 1] : [from.x, from.y];
        const start = anchorPoint(from, first[0], first[1]);
        const end = anchorPoint(to, last[0], last[1]);
        return [start, ...via, end];
      }

      function anchorSide(node, point) {
        const [x, y] = point;
        const eps = 1.5;
        if (Math.abs(x - (node.x - HALF_W)) <= eps) return "left";
        if (Math.abs(x - (node.x + HALF_W)) <= eps) return "right";
        if (Math.abs(y - (node.y - HALF_H)) <= eps) return "top";
        if (Math.abs(y - (node.y + HALF_H)) <= eps) return "bottom";

        const dx = x - node.x;
        const dy = y - node.y;
        if (Math.abs(dx) >= Math.abs(dy)) return dx < 0 ? "left" : "right";
        return dy < 0 ? "top" : "bottom";
      }

      function sideAxisValue(side, point) {
        return (side === "left" || side === "right") ? point[1] : point[0];
      }

      function offsetPointOnSide(point, side, offset) {
        if (side === "left" || side === "right") {
          return [point[0], point[1] + offset];
        }
        return [point[0] + offset, point[1]];
      }

      function adjustedEdgePointsMap() {
        const entries = [];
        edges.forEach((edge) => {
          const from = nodeMap[edge.from];
          const to = nodeMap[edge.to];
          if (!from || !to) return;
          const points = edgePoints(edge).map((pt) => [pt[0], pt[1]]);
          entries.push({ edge, from, to, points });
        });

        const groups = new Map();
        const pushGroup = (key, ref) => {
          if (!groups.has(key)) groups.set(key, []);
          groups.get(key).push(ref);
        };

        entries.forEach((entry, entryIndex) => {
          const start = entry.points[0];
          const end = entry.points[entry.points.length - 1];
          const startSide = anchorSide(entry.from, start);
          const endSide = anchorSide(entry.to, end);

          pushGroup(`${entry.from.id}|out|${startSide}`, {
            entryIndex,
            endpoint: "start",
            side: startSide,
            axis: sideAxisValue(startSide, start),
            kind: entry.edge.kind,
          });
          pushGroup(`${entry.to.id}|in|${endSide}`, {
            entryIndex,
            endpoint: "end",
            side: endSide,
            axis: sideAxisValue(endSide, end),
            kind: entry.edge.kind,
          });
        });

        const kindPriority = { sequential: 0, main: 1, cross: 2, input: 3, output: 4, fail: 5 };
        groups.forEach((refs) => {
          refs.sort((a, b) => {
            if (a.axis !== b.axis) return a.axis - b.axis;
            return (kindPriority[a.kind] ?? 99) - (kindPriority[b.kind] ?? 99);
          });
          const n = refs.length;
          if (n <= 1) return;
          refs.forEach((ref, idx) => {
            const slotOffset = (idx - (n - 1) / 2) * 8;
            const entry = entries[ref.entryIndex];
            const ptIndex = ref.endpoint === "start" ? 0 : (entry.points.length - 1);
            entry.points[ptIndex] = offsetPointOnSide(entry.points[ptIndex], ref.side, slotOffset);
          });
        });

        const out = new Map();
        entries.forEach((entry) => {
          out.set(entry.edge.id, entry.points);
        });
        return out;
      }

      function pointsToPath(points) {
        let d = `M ${points[0][0]} ${points[0][1]}`;
        for (let i = 1; i < points.length; i += 1) {
          d += ` L ${points[i][0]} ${points[i][1]}`;
        }
        return d;
      }

      function renderBlockPanel(node) {
        blockInspectorTitle.textContent = `${node.label} main details`;
        const insideList = (node.inside || []).map((item) => `<li>${item}</li>`).join("");
        blockInspectorBody.innerHTML =
          `<div class="k">Section role</div><div class="v">${node.role}</div>` +
          `<div class="k">Main purpose</div><div class="v">${node.detail}</div>` +
          `<div class="k">What is inside</div><ul>${insideList || "<li>No details</li>"}</ul>`;
      }

      async function setSidebarVisible(show) {
        sidebarVisible = show;
        app.classList.toggle("sidebar-hidden", !show);
        toggleExplorerBtn.textContent = show ? "Hide Explorer" : "Show Explorer";
        if (show && !treeLoaded) {
          const res = await fetch(`/api/tree?v=${encodeURIComponent(APP_VERSION)}&ts=${Date.now()}`, { cache: "no-store" });
          const data = await res.json();
          renderTree(data, treeWrap, 0);
          treeItems = [...treeWrap.querySelectorAll(".tree-item")];
          collapseAllDirs();
          treeLoaded = true;
        }
      }

      function edgeTechHtml(edge) {
        let html = "";
        if (edge.executor) {
          html += `<div class="k">Execution owner</div><div class="v">${edge.executor}</div>`;
        }
        if (edge.source) {
          html += `<div class="k">Source of constraints</div><div class="v">${edge.source}</div>`;
        }
        if (edge.note) {
          html += `<div class="k">Note</div><div class="v">${edge.note}</div>`;
        }
        return html;
      }

      function updateTechToggleText() {
        toggleTechBtn.textContent = showTechDetails ? "Hide technical details" : "Show technical details";
      }

      function edgeKindLabel(kind) {
        if (kind === "sequential" || kind === "main") return "Sequential step flow";
        if (kind === "cross") return "Cross-section dependency";
        if (kind === "input") return "Input decomposition";
        if (kind === "output") return "Output aggregation";
        if (kind === "fail") return "Failure path";
        return "Connection";
      }

      function buildLogicStepsFallback(payload) {
        const localNodes = Array.isArray(payload && payload.nodes) ? payload.nodes : [];
        const localEdges = Array.isArray(payload && payload.edges) ? payload.edges : [];
        const sectionNodes = localNodes
          .filter((n) => n && typeof n.id === "string" && /^S\d+$/.test(n.id))
          .sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1)));
        if (!sectionNodes.length) return "";

        const lines = ["Structured Logic Steps", "", "Step-by-step breakdown:"];
        sectionNodes.forEach((node, i) => {
          lines.push(`${i + 1}. ${node.label || `Section ${i + 1}`}`);
          lines.push(`   Purpose: ${node.detail || "Generated step."}`);
          const pts = Array.isArray(node.inside) ? node.inside.filter((p) => String(p || "").trim()).slice(0, 4) : [];
          if (pts.length) {
            lines.push("   Key points:");
            pts.forEach((p) => lines.push(`   - ${p}`));
          }
          lines.push("");
        });

        const depEdges = localEdges.filter((e) => e && /^S\d+$/.test(String(e.from || "")) && /^S\d+$/.test(String(e.to || "")));
        if (depEdges.length) {
          lines.push("Dependencies:");
          depEdges.forEach((edge) => {
            const fromIdx = Number(String(edge.from).slice(1));
            const toIdx = Number(String(edge.to).slice(1));
            const fromNode = sectionNodes.find((n) => n.id === edge.from);
            const toNode = sectionNodes.find((n) => n.id === edge.to);
            const fromLabel = fromNode ? fromNode.label : edge.from;
            const toLabel = toNode ? toNode.label : edge.to;
            const reason = edge.why || "Dependency in context.";
            lines.push(`- ${edgeKindLabel(edge.kind)}: [${fromIdx}] ${fromLabel} -> [${toIdx}] ${toLabel}. Reason: ${reason}`);
          });
          lines.push("");
        }
        return lines.join("\n").trim();
      }

      function resizeLogicStepsOutput() {
        if (!logicStepsOutput) return;
        logicStepsOutput.style.height = "auto";
        const target = Math.max(210, logicStepsOutput.scrollHeight || 0);
        logicStepsOutput.style.height = `${target}px`;
      }

      function updateLogicStepsText(payload) {
        if (!logicStepsOutput) return;
        const direct = payload && typeof payload.logic_steps_text === "string" ? payload.logic_steps_text.trim() : "";
        logicStepsOutput.value = direct || buildLogicStepsFallback(payload) || "";
        resizeLogicStepsOutput();
      }

      function setApiKeyConfigured(configured, text) {
        externalApiKeyConfigured = Boolean(configured);
        if (!apiKeyStatus) return;
        apiKeyStatus.textContent = text || (externalApiKeyConfigured ? "Configured for this session." : "Not set");
        apiKeyStatus.style.color = externalApiKeyConfigured ? "#7ee787" : "#8b949e";
      }

      async function refreshApiKeyStatus() {
        try {
          const res = await fetch(`/api/settings/openai-key-status?v=${encodeURIComponent(APP_VERSION)}&ts=${Date.now()}`, { cache: "no-store" });
          if (!res.ok) throw new Error("status request failed");
          const data = await res.json();
          setApiKeyConfigured(Boolean(data.configured));
        } catch (_) {
          setApiKeyConfigured(false, "Status unavailable");
        }
      }

      async function saveApiKeyForSession() {
        if (!apiKeyInput || !saveApiKeyBtn) return;
        const key = apiKeyInput.value.trim();
        const oldLabel = saveApiKeyBtn.textContent;
        saveApiKeyBtn.disabled = true;
        saveApiKeyBtn.textContent = "Saving...";
        try {
          const res = await fetch(`/api/settings/openai-key?v=${encodeURIComponent(APP_VERSION)}&ts=${Date.now()}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
            body: JSON.stringify({ openai_api_key: key }),
          });
          const data = await res.json().catch(() => ({}));
          if (!res.ok) {
            throw new Error(String(data.error || "Failed to save API key."));
          }
          if (data.configured) {
            setApiKeyConfigured(true, "Configured for this session.");
            statusEl.textContent = "API key set for this session.";
          } else {
            setApiKeyConfigured(false, "API key cleared.");
            statusEl.textContent = "API key cleared for this session.";
          }
          apiKeyInput.value = "";
        } catch (err) {
          const msg = err && err.message ? err.message : "unknown error";
          statusEl.textContent = `Failed to save API key: ${msg}`;
          setApiKeyConfigured(externalApiKeyConfigured, "Save failed");
        } finally {
          saveApiKeyBtn.disabled = false;
          saveApiKeyBtn.textContent = oldLabel;
        }
      }

      function stopProgressTickers() {
        if (progressTicker) {
          clearInterval(progressTicker);
          progressTicker = null;
        }
        if (progressStageTicker) {
          clearInterval(progressStageTicker);
          progressStageTicker = null;
        }
      }

      function startGenerationProgress(mode) {
        if (!progressBar || !progressText) return;
        stopProgressTickers();
        progressValue = 8;
        progressBar.classList.remove("success", "error");
        progressBar.classList.add("running");
        progressBar.style.width = `${progressValue}%`;

        const stages = mode === "external"
          ? [
              "Preparing request...",
              "Chunking and structuring context...",
              "Calling external API...",
              "Validating/repairing output...",
              "Building diagram payload...",
            ]
          : [
              "Preparing request...",
              "Chunking and structuring context...",
              "Calling local model/fallback...",
              "Validating/repairing output...",
              "Building diagram payload...",
            ];
        let stageIdx = 0;
        progressText.textContent = stages[stageIdx];

        progressStageTicker = setInterval(() => {
          stageIdx = Math.min(stageIdx + 1, stages.length - 1);
          progressText.textContent = stages[stageIdx];
        }, 3200);

        progressTicker = setInterval(() => {
          const inc = progressValue < 40 ? 7 : (progressValue < 72 ? 3.5 : 1.2);
          progressValue = Math.min(92, progressValue + inc);
          progressBar.style.width = `${progressValue}%`;
        }, 900);
      }

      function finishGenerationProgress(ok, message) {
        if (!progressBar || !progressText) return;
        stopProgressTickers();
        progressValue = 100;
        progressBar.style.width = "100%";
        progressBar.classList.remove("running", "success", "error");
        progressBar.classList.add(ok ? "success" : "error");
        progressText.textContent = message || (ok ? "Generation finished." : "Generation failed.");
      }

      function classifyGenerationFailure(statusCode, detail) {
        const detailText = (detail || "").trim();
        if (statusCode === 400) return detailText || "Invalid request (400). Check your input or provider settings.";
        if (statusCode === 401 || statusCode === 403) return "API key invalid or no permission (401/403). Check your API key and access.";
        if (statusCode === 408 || statusCode === 504) return "Provider timed out (408/504). Please retry.";
        if (statusCode === 429) return "Rate limit reached (429). Please wait and try again.";
        if (statusCode >= 500) return detailText || `Server/provider error (${statusCode}). Please retry later.`;
        return detailText || `Generation failed (HTTP ${statusCode}).`;
      }

      function inspectNode(node) {
        selectedNodeId = node.id;
        selectedEdgeId = null;
        inspectorTitle.textContent = node.label;
        inspectorBody.innerHTML =
          `<div class="k">Section</div><div class="v">${node.role}</div>` +
          `<div class="k">What does it do</div><div class="v">${node.detail}</div>`;
        renderBlockPanel(node);
        redrawSelection();
      }

      function inspectEdge(edge) {
        selectedEdgeId = edge.id;
        selectedNodeId = null;
        const fromNode = nodeMap[edge.from];
        const toNode = nodeMap[edge.to];
        if (!fromNode || !toNode) return;
        const from = fromNode.label;
        const to = toNode.label;
        inspectorTitle.textContent = `${from} -> ${to}`;
        const techHtml = edgeTechHtml(edge);
        const techBlock = (showTechDetails && techHtml)
          ? `<div class="k">Technical details</div>${techHtml}`
          : "";
        inspectorBody.innerHTML =
          `<div class="k">Connection type</div><div class="v">${edgeKindLabel(edge.kind)}</div>` +
          `<div class="k">Why connected</div><div class="v">${edge.why}</div>` +
          `<div class="k">What it does</div><div class="v">${edge.does}</div>` +
          techBlock +
          `<div class="k">Direction</div><div class="v">${from} to ${to}</div>`;
        redrawSelection();
      }

      function redrawSelection() {
        svg.querySelectorAll(".edge-visible").forEach((el) => {
          const hit = el.getAttribute("data-edge-id") === selectedEdgeId;
          el.classList.toggle("edge-selected", hit);
        });
        svg.querySelectorAll(".node-box").forEach((el) => {
          const hit = el.getAttribute("data-node-id") === selectedNodeId;
          el.classList.toggle("selected", hit);
        });
      }

      function resetInspectors() {
        selectedEdgeId = null;
        selectedNodeId = null;
        inspectorTitle.textContent = "Connection Details";
        inspectorBody.textContent = "No selection yet.";
        blockInspectorTitle.textContent = "Block Main Details";
        blockInspectorBody.textContent = "No block selected yet.";
      }

      function applyDiagramPayload(payload) {
        if (!payload || !Array.isArray(payload.nodes) || payload.nodes.length === 0) {
          throw new Error("Invalid diagram payload.");
        }
        const validNodeKinds = new Set(["main", "input", "output", "fail"]);
        const validEdgeKinds = new Set(["main", "input", "output", "fail", "sequential", "cross"]);
        nodes = payload.nodes.map((n, idx) => ({
          ...n,
          kind: validNodeKinds.has(n.kind) ? n.kind : "main",
          x: Number.isFinite(n.x) ? n.x : 560,
          y: Number.isFinite(n.y) ? n.y : 80 + idx * 80,
          inside: Array.isArray(n.inside) ? n.inside : [],
          role: n.role || "Structured section",
          detail: n.detail || "",
        }));
        edges = Array.isArray(payload.edges)
          ? payload.edges
            .filter((e) => e && e.from && e.to)
            .map((e) => ({
              ...e,
              kind: validEdgeKinds.has(e.kind) ? e.kind : "main",
            }))
          : [];
        nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));
        resetInspectors();
        updateLogicStepsText(payload);
        renderDiagram();

        if (payload.meta) {
          const strategy = payload.meta.strategy || "unknown";
          const chunks = payload.meta.chunk_count || 0;
          const sections = payload.meta.section_count || 0;
          const quality = payload.meta.quality_score || 0;
          const gate = payload.meta.quality_gate_passed ? "pass" : "retry/fallback";
          const consensus = payload.meta.consensus_strength || 0;
          const cross = payload.meta.cross_link_count || 0;
          const layout = payload.meta.layout_mode || "single_spine";
          const branches = payload.meta.main_branch_count || 1;
          builderNote.textContent = `Automation strategy: ${strategy}; layout=${layout}; branches=${branches}; chunks=${chunks}; sections=${sections}; cross-links=${cross}; quality=${quality}; gate=${gate}; consensus=${consensus}.`;
        }
      }

      async function generateDiagramFromInput() {
        const text = contextInput.value.trim();
        if (!text) {
          statusEl.textContent = "Paste context first, then click Send.";
          contextInput.focus();
          return;
        }

        const mode = modeSelect.value === "external" ? "external" : "local";
        if (mode === "external" && !externalApiKeyConfigured) {
          statusEl.textContent = "External mode requires API key. Paste key above and click Set Key.";
          if (apiKeyInput) apiKeyInput.focus();
          return;
        }
        const oldLabel = generateDiagramBtn.textContent;
        let timeoutId = null;
        generateDiagramBtn.disabled = true;
        generateDiagramBtn.textContent = "Sending...";
        statusEl.textContent = `Running pipeline (${mode})...`;
        startGenerationProgress(mode);

        try {
          const controller = new AbortController();
          timeoutId = setTimeout(() => controller.abort(), GENERATION_TIMEOUT_MS);
          const res = await fetch(`/api/diagram/generate?v=${encodeURIComponent(APP_VERSION)}&ts=${Date.now()}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
            signal: controller.signal,
            body: JSON.stringify({
              text,
              mode,
              allow_llm: true,
              llm_attempts: 2,
            }),
          });
          const data = await res.json().catch(() => ({}));
          if (!res.ok) {
            throw new Error(classifyGenerationFailure(res.status, String(data.error || "")));
          }
          applyDiagramPayload(data);
          setView("diagram");
          const fallback = data.meta && data.meta.fallback_used ? " (fallback)" : "";
          const sections = data.meta && data.meta.section_count ? data.meta.section_count : "n/a";
          statusEl.textContent = `Diagram generated with ${sections} sections${fallback}.`;
          finishGenerationProgress(true, fallback ? `Completed with fallback. Sections=${sections}.` : `Completed successfully. Sections=${sections}.`);
        } catch (err) {
          if (err && err.name === "AbortError") {
            const timeoutMsg = `Generation timed out after ${Math.round(GENERATION_TIMEOUT_MS / 1000)}s. Provider may be stuck or slow.`;
            statusEl.textContent = timeoutMsg;
            finishGenerationProgress(false, timeoutMsg);
          } else {
            const msg = err && err.message ? err.message : "unknown error";
            statusEl.textContent = `Generation failed: ${msg}`;
            finishGenerationProgress(false, `Failed: ${msg}`);
          }
        } finally {
          if (timeoutId) clearTimeout(timeoutId);
          generateDiagramBtn.disabled = false;
          generateDiagramBtn.textContent = oldLabel;
        }
      }

      function renderDiagram() {
        svg.innerHTML = "";
        if (!nodes.length) {
          const emptyHint = createSvgEl("text", {
            x: 575,
            y: 450,
            "text-anchor": "middle",
            fill: "#8b949e",
            "font-size": 15,
            "font-family": "Segoe UI, system-ui, sans-serif",
            "font-weight": 600,
          });
          emptyHint.textContent = "Empty canvas. Paste context and click Send to generate a diagram.";
          svg.appendChild(emptyHint);
          return;
        }

        const defs = createSvgEl("defs", {});
        Object.entries(styles).forEach(([kind, style]) => {
          const marker = createSvgEl("marker", {
            id: `arrow-${kind}`, viewBox: "0 0 10 10", refX: "9", refY: "5",
            markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse",
          });
          marker.appendChild(createSvgEl("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: style.edge }));
          defs.appendChild(marker);
        });
        svg.appendChild(defs);

        const edgePointMap = adjustedEdgePointsMap();
        edges.forEach((edge) => {
          const pts = edgePointMap.get(edge.id) || edgePoints(edge);
          const path = pointsToPath(pts);
          const edgeStyle = styles[edge.kind] || styles.main;
          const color = edgeStyle.edge;
          const markerKind = styles[edge.kind] ? edge.kind : "main";

          const visible = createSvgEl("path", {
            d: path,
            class: "edge-visible",
            stroke: color,
            "data-edge-id": edge.id,
            "marker-end": `url(#arrow-${markerKind})`,
          });
          if (edge.kind === "input") visible.setAttribute("stroke-dasharray", "6 5");
          if (edge.kind === "cross") visible.setAttribute("stroke-dasharray", "4 4");
          svg.appendChild(visible);

          const hit = createSvgEl("path", {
            d: path,
            class: "edge-hit",
            "data-edge-id": edge.id,
          });
          hit.addEventListener("click", (evt) => {
            evt.stopPropagation();
            inspectEdge(edge);
          });
          svg.appendChild(hit);
        });

        nodes.forEach((node) => {
          const g = createSvgEl("g", { class: "node-box", "data-node-id": node.id });
          const style = styles[node.kind];
          const rect = createSvgEl("rect", {
            x: node.x - HALF_W,
            y: node.y - HALF_H,
            width: NODE_W,
            height: NODE_H,
            rx: 8,
            fill: style.fill,
            stroke: style.stroke,
            "stroke-width": 1.8,
          });
          const text = createSvgEl("text", {
            x: node.x,
            y: node.y + 4,
            "text-anchor": "middle",
            fill: style.text,
            "font-size": 13,
            "font-family": "Segoe UI, system-ui, sans-serif",
            "font-weight": 600,
          });
          text.textContent = node.label;
          g.appendChild(rect);
          g.appendChild(text);
          g.addEventListener("click", (evt) => {
            evt.stopPropagation();
            inspectNode(node);
          });
          svg.appendChild(g);
        });

        // Legend
        const legend = createSvgEl("g", {});
        legend.appendChild(createSvgEl("rect", { x: 12, y: 790, width: 11, height: 11, fill: styles.sequential.fill, stroke: styles.sequential.stroke }));
        let t = createSvgEl("text", { x: 28, y: 799, class: "legend" });
        t.textContent = "Sequential flow";
        legend.appendChild(t);

        legend.appendChild(createSvgEl("rect", { x: 118, y: 790, width: 11, height: 11, fill: styles.cross.fill, stroke: styles.cross.stroke }));
        t = createSvgEl("text", { x: 134, y: 799, class: "legend" });
        t.textContent = "Cross dependency";
        legend.appendChild(t);

        legend.appendChild(createSvgEl("rect", { x: 250, y: 790, width: 11, height: 11, fill: styles.input.fill, stroke: styles.input.stroke }));
        t = createSvgEl("text", { x: 266, y: 799, class: "legend" });
        t.textContent = "Input source";
        legend.appendChild(t);

        legend.appendChild(createSvgEl("rect", { x: 354, y: 790, width: 11, height: 11, fill: styles.output.fill, stroke: styles.output.stroke }));
        t = createSvgEl("text", { x: 370, y: 799, class: "legend" });
        t.textContent = "Output";
        legend.appendChild(t);

        legend.appendChild(createSvgEl("rect", { x: 424, y: 790, width: 11, height: 11, fill: styles.fail.fill, stroke: styles.fail.stroke }));
        t = createSvgEl("text", { x: 440, y: 799, class: "legend" });
        t.textContent = "Failure branch";
        legend.appendChild(t);
        svg.appendChild(legend);

        svg.onclick = () => {
          resetInspectors();
          redrawSelection();
        };
      }

      function escapeHtml(text) {
        return text
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;");
      }

      async function openFile(path, ext, el) {
        treeWrap.querySelectorAll(".tree-item.active").forEach((item) => item.classList.remove("active"));
        if (el) el.classList.add("active");
        setView("file");
        statusEl.textContent = "File Viewer";

        const res = await fetch(`/api/file/${encodeURIComponent(path)}?v=${encodeURIComponent(APP_VERSION)}&ts=${Date.now()}`, { cache: "no-store" });
        const data = await res.json();
        fileMeta.innerHTML = `<span class="badge" style="background:${(ext && {
          md: "#1a7f37", json: "#6f42c1", yaml: "#d4a017", yml: "#d4a017",
          py: "#3572a5", sas: "#b07219", r: "#198ce7", sql: "#e38c00",
        }[ext]) || "#666"}">${(ext || "file").toUpperCase()}</span>&nbsp;&nbsp;${data.path}`;
        fileContent.innerHTML = escapeHtml(data.content);
      }

      function renderTree(nodesData, parent, depth) {
        nodesData.forEach((node) => {
          const row = document.createElement("div");
          row.className = "tree-item";
          row.style.paddingLeft = `${10 + depth * 16}px`;
          row.dataset.path = node.path;
          row.dataset.type = node.type;
          row.dataset.name = node.name.toLowerCase();

          const icon = document.createElement("span");
          icon.className = "icon";
          const label = document.createElement("span");
          label.className = "tree-label";
          label.textContent = node.name;

          if (node.type === "dir") {
            icon.textContent = ">";
            row.append(icon, label);
            parent.appendChild(row);
            const childrenWrap = document.createElement("div");
            childrenWrap.className = "tree-children collapsed";
            parent.appendChild(childrenWrap);
            row.addEventListener("click", () => {
              childrenWrap.classList.toggle("collapsed");
              icon.textContent = childrenWrap.classList.contains("collapsed") ? ">" : "v";
            });
            renderTree(node.children || [], childrenWrap, depth + 1);
          } else {
            icon.textContent = "-";
            row.append(icon, label);
            parent.appendChild(row);
            row.addEventListener("click", () => openFile(node.path, node.ext, row));
          }
        });
      }

      function collapseAllDirs() {
        treeWrap.querySelectorAll('.tree-item[data-type="dir"]').forEach((row) => {
          const childrenWrap = row.nextElementSibling;
          if (childrenWrap && childrenWrap.classList.contains("tree-children")) {
            childrenWrap.classList.add("collapsed");
          }
          const icon = row.querySelector(".icon");
          if (icon) icon.textContent = ">";
        });
      }

      function expandAllDirs() {
        treeWrap.querySelectorAll('.tree-item[data-type="dir"]').forEach((row) => {
          const childrenWrap = row.nextElementSibling;
          if (childrenWrap && childrenWrap.classList.contains("tree-children")) {
            childrenWrap.classList.remove("collapsed");
          }
          const icon = row.querySelector(".icon");
          if (icon) icon.textContent = "v";
        });
      }

      function setupSearch() {
        searchBox.addEventListener("input", () => {
          if (!treeLoaded) return;
          const q = searchBox.value.trim().toLowerCase();
          treeItems.forEach((item) => {
            if (!q) {
              item.classList.remove("hidden");
              return;
            }
            if (item.dataset.type === "dir") {
              item.classList.remove("hidden");
              return;
            }
            const hit = item.dataset.path.toLowerCase().includes(q);
            item.classList.toggle("hidden", !hit);
          });
          if (!q) {
            collapseAllDirs();
            return;
          }
          expandAllDirs();
        });
      }

      function setupResize() {
        const handle = $("resize-handle");
        const sidebar = $("sidebar");
        let dragging = false;
        handle.addEventListener("mousedown", () => {
          dragging = true;
          document.body.style.cursor = "col-resize";
          document.body.style.userSelect = "none";
        });
        document.addEventListener("mousemove", (evt) => {
          if (!dragging) return;
          const w = Math.max(220, Math.min(620, evt.clientX));
          sidebar.style.width = `${w}px`;
        });
        document.addEventListener("mouseup", () => {
          dragging = false;
          document.body.style.cursor = "";
          document.body.style.userSelect = "";
        });
      }

      async function checkVersionUpdate() {
        try {
          const res = await fetch(`/api/version?ts=${Date.now()}`, { cache: "no-store" });
          if (!res.ok) return;
          const data = await res.json();
          const latest = data.version || "";
          if (latest && latest !== APP_VERSION) {
            statusEl.textContent = `New version detected (${latest}), reloading...`;
            const next = new URL(window.location.href);
            next.searchParams.set("v", latest);
            setTimeout(() => window.location.replace(next.toString()), 300);
          }
        } catch (_) {
          // ignore transient network errors
        }
      }

      function startVersionWatcher() {
        setInterval(checkVersionUpdate, 8000);
      }

      tabDiagram.addEventListener("click", () => {
        setView("diagram");
        statusEl.textContent = "Paste context and click Send to generate. The canvas is empty by default.";
      });
      tabFile.addEventListener("click", () => {
        setView("file");
        statusEl.textContent = "File Viewer";
      });
      saveApiKeyBtn.addEventListener("click", async () => {
        await saveApiKeyForSession();
      });
      apiKeyInput.addEventListener("keydown", async (evt) => {
        if (evt.key === "Enter") {
          evt.preventDefault();
          await saveApiKeyForSession();
        }
      });
      generateDiagramBtn.addEventListener("click", async () => {
        await generateDiagramFromInput();
      });
      contextInput.addEventListener("keydown", async (evt) => {
        if ((evt.ctrlKey || evt.metaKey) && evt.key === "Enter") {
          evt.preventDefault();
          await generateDiagramFromInput();
        }
      });
      exportDiagramBtn.addEventListener("click", async () => {
        await exportDiagramPng();
      });
      toggleExplorerBtn.addEventListener("click", async () => {
        await setSidebarVisible(!sidebarVisible);
      });
      toggleTechBtn.addEventListener("click", () => {
        showTechDetails = !showTechDetails;
        updateTechToggleText();
        if (selectedEdgeId) {
          const edge = edges.find((item) => item.id === selectedEdgeId);
          if (edge) inspectEdge(edge);
        }
      });

      async function init() {
        nodes = [];
        edges = [];
        nodeMap = {};
        resetInspectors();
        if (logicStepsOutput) {
          logicStepsOutput.value = "";
          resizeLogicStepsOutput();
        }
        if (progressBar && progressText) {
          stopProgressTickers();
          progressBar.classList.remove("running", "success", "error");
          progressBar.style.width = "0%";
          progressText.textContent = "Ready.";
        }
        renderDiagram();
        setupResize();
        setupSearch();
        updateTechToggleText();
        await refreshApiKeyStatus();
        await setSidebarVisible(false);
        versionEl.textContent = `v${APP_VERSION}`;
        setView("diagram");
        statusEl.textContent = "Paste context and click Send to run the full pipeline.";
        startVersionWatcher();
      }

      init();
    })();
  </script>
</body>
</html>
"""


def main():
    os.chdir(ROOT)
    server = ThreadedHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}/?v={APP_VERSION}"
    print(f"\nIdeal-Now Diagram Web UI")
    print(f"{url}")
    print(f"version: {APP_VERSION}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
