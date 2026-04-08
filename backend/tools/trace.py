"""Raster-to-SVG tracing using vtracer."""

from pathlib import Path
import vtracer


def trace_to_svg(
    input_path: str,
    output_dir: str,
    color_precision: int = 6,
    filter_speckle: int = 4,
    corner_threshold: int = 60,
) -> str:
    """Convert a raster image to SVG using vtracer."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}.svg"

    vtracer.convert_image_to_svg_py(
        str(inp),
        str(out),
        colormode="color",
        hierarchical="stacked",
        mode="spline",
        filter_speckle=filter_speckle,
        color_precision=color_precision,
        layer_difference=16,
        corner_threshold=corner_threshold,
        length_threshold=4.0,
        max_iterations=10,
        splice_threshold=45,
        path_precision=3,
    )
    return str(out)
