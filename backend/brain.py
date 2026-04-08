"""Natural-language command parser.

Keyword-based for now — swap in Ollama + gemma3 later.
"""

import re


def _extract_layer(msg: str, layers: list[str] | None, active_layer: str | None) -> str:
    """Try to find a layer name in the message, fall back to active layer."""
    if layers:
        for name in layers:
            if name.lower() in msg:
                return name
    return active_layer or "Layer 1"


def _extract_color(msg: str) -> str:
    """Extract a hex color or color name from the message."""
    # Hex color
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


def parse_command(
    message: str,
    layers: list[str] | None = None,
    active_layer: str | None = None,
) -> dict:
    """Parse a chat message into a structured tool action."""
    msg = message.lower().strip()
    layer = _extract_layer(msg, layers, active_layer)

    # Order matters — check more specific patterns first
    if "sticker" in msg:
        return {"tool": "sticker_pack", "layer": layer, "params": {}}

    if "remove" in msg and "background" in msg:
        return {"tool": "remove_bg", "layer": layer, "params": {}}

    if "segment" in msg or "extract" in msg:
        return {"tool": "segment", "layer": layer, "params": {}}

    if "mask" in msg:
        return {"tool": "mask", "layer": layer, "params": {}}

    if "clean" in msg or "outline" in msg:
        return {"tool": "cleanup", "layer": layer, "params": {}}

    if "trace" in msg or "svg" in msg or "vector" in msg:
        return {"tool": "trace", "layer": layer, "params": {}}

    if ("color" in msg or "fill" in msg) and ("select" not in msg):
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
