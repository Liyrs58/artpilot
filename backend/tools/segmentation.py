"""Subject segmentation using rembg as a lightweight SAM alternative."""

from pathlib import Path
from rembg import remove, new_session
from PIL import Image


# Use the u2net model for segmentation masks
_session = None


def _get_session():
    global _session
    if _session is None:
        _session = new_session("u2net")
    return _session


def segment_subject(input_path: str, output_dir: str) -> str:
    """Segment the main subject from the image."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}_segment.png"

    img = Image.open(inp)
    result = remove(img, session=_get_session())
    result.save(out)
    return str(out)


def extract_mask(input_path: str, output_dir: str) -> str:
    """Extract an alpha mask of the main subject."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}_mask.png"

    img = Image.open(inp)
    result = remove(img, session=_get_session(), only_mask=True)
    result.save(out)
    return str(out)
