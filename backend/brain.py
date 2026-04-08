"""LLM-powered command parser using Ollama.

Sends the user message + document structure to a local LLM,
which generates ExtendScript code to execute in Illustrator.
Falls back to keyword parsing if Ollama is unavailable.
"""

import re
import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"  # or gemma3:4b

SYSTEM_PROMPT = """You are ArtPilot, an AI assistant inside Adobe Illustrator. You receive:
1. A user request in natural language
2. The document structure (layers, items with types, positions, sizes, colors)

Your job: output ONLY valid ExtendScript (JavaScript for Illustrator) that fulfills the request. No explanation, no markdown, no comments — just the code.

Available globals:
- app.activeDocument (the open document)
- app.activeDocument.layers[i] (layers)
- layer.pageItems[i] (items on a layer)
- item.typename: "PathItem", "CompoundPathItem", "GroupItem", "PlacedItem", "RasterItem"
- item.name, item.left, item.top, item.width, item.height
- item.fillColor (set via new RGBColor() with .red .green .blue 0-255)
- item.strokeColor, item.strokeWidth
- item.remove() to delete
- doc.selection = [items] to select items

Key patterns:
- To fill a specific item: var c = new RGBColor(); c.red=R; c.green=G; c.blue=B; item.fillColor = c;
- To fill items in a group: iterate group.pageItems
- To target by position/size: compare item.left, item.top, item.width, item.height
- Items with larger area are typically backgrounds/dresses; smaller items are details/accessories
- "skin" usually means the body/mannequin paths (often lighter fill colors or specific named items)
- "dress"/"clothing" usually means the largest path items on the layer
- To select items: push them into an array and assign to doc.selection

Always wrap code in a try/catch and return a result string.
Output ONLY the code. No markdown fences."""


def _call_ollama(message: str, doc_info: str) -> str | None:
    """Call Ollama and return the generated ExtendScript code."""
    prompt = f"""User request: {message}

Document structure:
{doc_info}

Generate ExtendScript code to fulfill this request. Output ONLY the code."""

    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 1024},
            },
            timeout=30.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            code = data.get("response", "").strip()
            # Strip markdown fences if the model adds them
            code = re.sub(r"^```(?:javascript|jsx|js)?\s*\n?", "", code)
            code = re.sub(r"\n?```\s*$", "", code)
            return code.strip()
    except Exception:
        pass
    return None


def _ollama_available() -> bool:
    """Quick check if Ollama is running."""
    try:
        resp = httpx.get("http://127.0.0.1:11434/api/tags", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


# ── Keyword fallback (same as before) ────────────────────

def _extract_layer(msg: str, layers: list[str] | None, active_layer: str | None) -> str:
    if layers:
        for name in layers:
            pattern = r'\b' + re.escape(name.lower()) + r'\b'
            if re.search(pattern, msg):
                return name
        if "background" in msg:
            return layers[-1]
    return active_layer or "Layer 1"


def _extract_color(msg: str) -> str:
    match = re.search(r"#([0-9a-fA-F]{6})", msg)
    if match:
        return "#" + match.group(1)
    color_map = {
        "red": "#FF0000", "green": "#00FF00", "blue": "#0000FF",
        "yellow": "#FFFF00", "white": "#FFFFFF", "black": "#000000",
        "orange": "#FF8800", "purple": "#8800FF", "pink": "#FF69B4",
        "cyan": "#00FFFF", "magenta": "#FF00FF", "gray": "#888888",
        "grey": "#888888",
    }
    for name, hex_val in color_map.items():
        if name in msg:
            return hex_val
    return "#FF0000"


def _extract_axis(msg: str) -> str:
    if "vertical" in msg or "vert" in msg:
        return "vertical"
    return "horizontal"


def parse_command_keyword(
    message: str,
    layers: list[str] | None = None,
    active_layer: str | None = None,
) -> dict:
    """Keyword-based fallback parser."""
    msg = message.lower().strip()
    layer = _extract_layer(msg, layers, active_layer)

    has_color_intent = any(w in msg for w in ["color", "fill", "paint", "change", "make"])
    has_color_word = any(w in msg for w in [
        "red", "green", "blue", "yellow", "white", "black", "orange",
        "purple", "pink", "cyan", "magenta", "gray", "grey", "#",
    ])

    if "sticker" in msg:
        return {"tool": "sticker_pack", "layer": layer, "params": {}}
    if "remove" in msg and "background" in msg and not (has_color_intent and has_color_word):
        return {"tool": "remove_bg", "layer": layer, "params": {}}
    if "segment" in msg or "extract" in msg:
        return {"tool": "segment", "layer": layer, "params": {}}
    if "mask" in msg:
        return {"tool": "mask", "layer": layer, "params": {}}
    if "clean" in msg or "outline" in msg:
        return {"tool": "cleanup", "layer": layer, "params": {}}
    if "trace" in msg or "svg" in msg or "vector" in msg:
        return {"tool": "trace", "layer": layer, "params": {}}
    if has_color_intent or has_color_word:
        color = _extract_color(msg)
        return {"tool": "fill", "layer": layer, "params": {"color": color}}
    if "flip" in msg or "mirror" in msg:
        axis = _extract_axis(msg)
        return {"tool": "flip", "layer": layer, "params": {"axis": axis}}
    if "duplicate" in msg or "copy" in msg or "clone" in msg:
        return {"tool": "duplicate", "layer": layer, "params": {}}
    if "delete" in msg or "remove layer" in msg:
        return {"tool": "delete", "layer": layer, "params": {}}
    if "select" in msg:
        return {"tool": "select", "layer": layer, "params": {}}
    if "export all" in msg:
        return {"tool": "export_all", "layer": layer, "params": {}}
    if "export" in msg:
        return {"tool": "export", "layer": layer, "params": {}}
    if "list" in msg or "layers" in msg:
        return {"tool": "list_layers", "layer": layer, "params": {}}

    return {"tool": "unknown", "layer": layer, "params": {}, "raw": message}


def parse_command(
    message: str,
    layers: list[str] | None = None,
    active_layer: str | None = None,
    doc_info: str | None = None,
) -> dict:
    """Parse with LLM if available, fall back to keywords."""
    if doc_info and _ollama_available():
        code = _call_ollama(message, doc_info)
        if code:
            return {"tool": "llm_script", "layer": active_layer or "Layer 1", "params": {"script": code}}

    return parse_command_keyword(message, layers, active_layer)
