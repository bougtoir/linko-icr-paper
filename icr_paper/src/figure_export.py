"""Export the manuscript figures as separate journal-ready files.

Statistics in Medicine asks for figures as separate files at publication
resolution. The analysis writes 600 dpi PNGs; this module copies each figure
cited in the manuscript into ``figures/submission/`` as ``Figure_N.tif``
(LZW-compressed) and ``Figure_N.png`` with the resolution recorded.
"""

from pathlib import Path

import pandas as pd
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
SUBMISSION_DIR = BASE_DIR / "figures" / "submission"
DPI = 600


def export_submission_figures(figure_specs: list) -> pd.DataFrame:
    """Write one TIFF and one PNG per manuscript figure and return the index."""
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in figure_specs:
        source = Path(spec["path"])
        if not source.exists():
            raise FileNotFoundError(f"Figure not generated: {source}")
        stem = spec["label"].replace(" ", "_")
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            tif_path = SUBMISSION_DIR / f"{stem}.tif"
            png_path = SUBMISSION_DIR / f"{stem}.png"
            rgb.save(tif_path, format="TIFF", compression="tiff_lzw",
                     dpi=(DPI, DPI))
            rgb.save(png_path, format="PNG", dpi=(DPI, DPI))
            width, height = image.size
        rows.append({
            "label": spec["label"],
            "source": source.name,
            "tiff": tif_path.name,
            "png": png_path.name,
            "pixels_width": width,
            "pixels_height": height,
            "dpi": DPI,
            "width_mm": round(width / DPI * 25.4, 1),
            "caption": spec["caption"],
        })
    index = pd.DataFrame(rows)
    index.to_csv(SUBMISSION_DIR / "figure_index.csv", index=False)
    return index
