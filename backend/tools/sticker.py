"""Sticker pack generator — remove bg, add white border, export."""

from pathlib import Path
from PIL import Image, ImageFilter
from rembg import remove


def make_sticker(input_path: str, output_dir: str, border_px: int = 12) -> str:
    """Create a sticker: remove bg, add white outline border, save PNG."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}_sticker.png"

    # Remove background
    img = Image.open(inp)
    subject = remove(img)

    # Create white border from alpha channel
    alpha = subject.split()[-1]
    # Dilate alpha to create border
    dilated = alpha.filter(ImageFilter.MaxFilter(border_px))

    # White canvas behind subject
    border_layer = Image.new("RGBA", subject.size, (255, 255, 255, 0))
    white = Image.new("RGBA", subject.size, (255, 255, 255, 255))
    border_layer.paste(white, mask=dilated)
    border_layer.paste(subject, mask=alpha)

    border_layer.save(out)
    return str(out)
