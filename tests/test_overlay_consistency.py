import base64
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

from supersonic_atomizer.plotting import generate_overlay_plots
from supersonic_atomizer.gui.plot_utils import figure_to_base64


def _image_bytes_from_base64(b64: str) -> bytes:
    return base64.b64decode(b64)


def test_overlay_png_matches_gui_render(tmp_path: Path):
    """Generate overlays from a provided overlay_series and assert the
    on-disk PNG is visually identical to the GUI-rendered PNG for the
    same series. Comparing pixels instead of raw PNG bytes avoids
    failures due to metadata differences in the PNG container.
    """
    overlay_series = {
        "temperature": {
            "title": "Temperature",
            "x_label": "x (m)",
            "ylabel": "Temperature (K)",
            "series": [
                {"label": "run1", "x": [0.0, 0.5, 1.0], "y": [300.0, 320.0, 340.0]},
                {"label": "run2", "x": [0.0, 0.5, 1.0], "y": [310.0, 330.0, 350.0]},
            ],
        },
        "pressure": {
            "title": "Pressure",
            "x_label": "x (m)",
            "ylabel": "Pressure (Pa)",
            "series": [
                {"label": "run1", "x": [0.0, 0.5, 1.0], "y": [1e5, 9e4, 8e4]},
            ],
        },
    }

    out_dir = tmp_path / "plots"
    out_dir.mkdir()

    # Call writer with empty labeled_results but provide overlay_series
    generate_overlay_plots(labeled_results=[], case_plots_directory=out_dir, overlay_series=overlay_series)

    for field, meta in overlay_series.items():
        saved_path = out_dir / f"{field}_overlay.png"
        assert saved_path.is_file(), f"Missing overlay file: {saved_path}"

        # Render GUI-style in-memory figure
        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        for s in meta["series"]:
            ax.plot(s["x"], s["y"], label=s.get("label"))
        ax.set_xlabel(meta["x_label"])
        ax.set_ylabel(meta["ylabel"])
        ax.set_title(meta["title"])
        ax.grid(True, alpha=0.3)
        if len(meta["series"]) > 1:
            ax.legend(fontsize="small")
        plt.tight_layout()

        gui_b64 = figure_to_base64(fig)
        plt.close(fig)

        # Load images and compare pixels (RGBA) to avoid byte-level PNG differences
        saved_img = Image.open(saved_path).convert("RGBA")
        gui_img = Image.open(io.BytesIO(_image_bytes_from_base64(gui_b64))).convert("RGBA")

        assert saved_img.size == gui_img.size, f"Image size mismatch for {field}"
        import numpy as np

        sa = np.array(saved_img)
        ga = np.array(gui_img)
        diff = np.abs(sa.astype(int) - ga.astype(int))
        mean_diff = float(diff.mean())
        # Allow small numeric differences due to anti-aliasing/font rasterization
        # while ensuring overall visual similarity.
        assert mean_diff < 3.0, f"Visual mean pixel diff too large for {field}: mean={mean_diff}"
