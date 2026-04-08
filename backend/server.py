"""ArtPilot FastAPI backend.

Flow:
  1. CEP panel sends POST /chat with {message, layers, active_layer}
  2. brain.py parses NL → structured action
  3. Tool runs (rembg, opencv, vtracer, etc.)
  4. Returns {reply, script} where script is ExtendScript for the panel to execute
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain import parse_command
from tools.background_removal import remove_background
from tools.segmentation import segment_subject, extract_mask
from tools.cleanup import cleanup_lines
from tools.sticker import make_sticker
from tools.trace import trace_to_svg
from tools.colorize import colorize

app = FastAPI(title="ArtPilot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temp directory for tool outputs
WORK_DIR = os.environ.get("ARTPILOT_WORK_DIR", tempfile.mkdtemp(prefix="artpilot_"))
Path(WORK_DIR).mkdir(parents=True, exist_ok=True)

# Where Illustrator exports layers for processing
EXPORT_DIR = os.environ.get("ARTPILOT_EXPORT_DIR", os.path.join(WORK_DIR, "exports"))
Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)


class ChatRequest(BaseModel):
    message: str
    layers: list[str] | None = None
    active_layer: str | None = None


class ChatResponse(BaseModel):
    reply: str
    script: str | None = None


def _layer_png(layer_name: str) -> str:
    """Expected path for an exported layer PNG."""
    return os.path.join(EXPORT_DIR, f"{layer_name}.png")


def _esc(s: str) -> str:
    """Escape a string for embedding in ExtendScript."""
    return s.replace("\\", "\\\\").replace("'", "\\'")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    action = parse_command(req.message, req.layers, req.active_layer)
    tool = action["tool"]
    layer = action["layer"]
    params = action["params"]
    input_path = _layer_png(layer)

    # ── ExtendScript-only tools (no image processing) ─────

    if tool == "select":
        return ChatResponse(
            reply=f"Selecting layer '{layer}'.",
            script=f"selectLayer('{_esc(layer)}')",
        )

    if tool == "delete":
        return ChatResponse(
            reply=f"Deleting layer '{layer}'.",
            script=f"deleteLayer('{_esc(layer)}')",
        )

    if tool == "duplicate":
        return ChatResponse(
            reply=f"Duplicating layer '{layer}'.",
            script=f"duplicateLayer('{_esc(layer)}')",
        )

    if tool == "flip":
        axis = params.get("axis", "horizontal")
        return ChatResponse(
            reply=f"Flipping '{layer}' {axis}.",
            script=f"flipLayer('{_esc(layer)}', '{axis}')",
        )

    if tool == "fill":
        color = params.get("color", "#FF0000")
        return ChatResponse(
            reply=f"Filling selection on '{layer}' with {color}.",
            script=f"fillSelection('{color}')",
        )

    if tool == "list_layers":
        return ChatResponse(
            reply="Listing layers.",
            script="listLayers()",
        )

    if tool == "export":
        return ChatResponse(
            reply=f"Exporting '{layer}' as PNG.",
            script=f"exportLayerAsPNG('{_esc(layer)}', '{_esc(EXPORT_DIR)}')",
        )

    if tool == "export_all":
        return ChatResponse(
            reply="Exporting all layers as PNG.",
            script=f"exportAllLayersAsPNG('{_esc(EXPORT_DIR)}')",
        )

    # ── Image-processing tools ────────────────────────────
    # These expect the layer to already be exported as a PNG.
    # The panel should export first, then call the tool.

    if not os.path.exists(input_path):
        # Ask the panel to export first, then retry
        return ChatResponse(
            reply=f"I need to export '{layer}' first. Exporting now — please resend your command after.",
            script=f"exportLayerAsPNG('{_esc(layer)}', '{_esc(EXPORT_DIR)}')",
        )

    if tool == "remove_bg":
        result = remove_background(input_path, WORK_DIR)
        return ChatResponse(
            reply=f"Background removed from '{layer}'.",
            script=f"placePNG('{_esc(result)}', '{_esc(layer)} no bg')",
        )

    if tool == "segment":
        result = segment_subject(input_path, WORK_DIR)
        return ChatResponse(
            reply=f"Segmented subject from '{layer}'.",
            script=f"placePNG('{_esc(result)}', '{_esc(layer)} segment')",
        )

    if tool == "mask":
        result = extract_mask(input_path, WORK_DIR)
        return ChatResponse(
            reply=f"Extracted mask from '{layer}'.",
            script=f"placePNG('{_esc(result)}', '{_esc(layer)} mask')",
        )

    if tool == "cleanup":
        result = cleanup_lines(input_path, WORK_DIR)
        return ChatResponse(
            reply=f"Cleaned up lines on '{layer}'.",
            script=f"placePNG('{_esc(result)}', '{_esc(layer)} clean')",
        )

    if tool == "sticker_pack":
        result = make_sticker(input_path, WORK_DIR)
        return ChatResponse(
            reply=f"Sticker created from '{layer}'.",
            script=f"placePNG('{_esc(result)}', '{_esc(layer)} sticker')",
        )

    if tool == "trace":
        result = trace_to_svg(input_path, WORK_DIR)
        return ChatResponse(
            reply=f"Traced '{layer}' to SVG at {result}.",
            script=None,  # SVG can be opened manually or placed via File > Place
        )

    # Unknown
    return ChatResponse(
        reply=f"I didn't understand that. Try: remove background, clean lines, make sticker, trace to SVG, flip, fill, export, delete, duplicate, select.",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
