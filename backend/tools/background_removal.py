"""Background removal using rembg."""

from pathlib import Path
from rembg import remove
from PIL import Image


def remove_background(input_path: str, output_dir: str) -> str:
    """Remove background from an image, return path to result PNG."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}_nobg.png"

    img = Image.open(inp)
    result = remove(img)
    result.save(out)
    return str(out)
