from pathlib import Path
import io
import base64
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from supersonic_atomizer.plotting import generate_overlay_plots
from supersonic_atomizer.gui.plot_utils import figure_to_base64

overlay_series = {
    "temperature": {
        "title": "Temperature",
        "x_label": "x (m)",
        "ylabel": "Temperature (K)",
        "series": [
            {"label": "run1", "x": [0.0, 0.5, 1.0], "y": [300.0, 320.0, 340.0]},
            {"label": "run2", "x": [0.0, 0.5, 1.0], "y": [310.0, 330.0, 350.0]},
        ],
    }
}

out_dir = Path('tmp_plots')
if out_dir.exists():
    import shutil
    shutil.rmtree(out_dir)
out_dir.mkdir()

generate_overlay_plots(labeled_results=[], case_plots_directory=out_dir, overlay_series=overlay_series)

field = 'temperature'
saved_path = out_dir / f"{field}_overlay.png"
# render GUI in-memory
fig, ax = plt.subplots(figsize=(6.5, 3.5))
for s in overlay_series[field]['series']:
    ax.plot(s['x'], s['y'], label=s.get('label'))
ax.set_xlabel(overlay_series[field]['x_label'])
ax.set_ylabel(overlay_series[field]['ylabel'])
ax.set_title(overlay_series[field]['title'])
ax.grid(True, alpha=0.3)
if len(overlay_series[field]['series']) > 1:
    ax.legend(fontsize='small')
plt.tight_layout()

buf = io.BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight', dpi=96)
buf.seek(0)
with open(out_dir / 'gui_image.png','wb') as f:
    f.write(buf.getvalue())
plt.close(fig)

saved = Image.open(saved_path).convert('RGBA')
gui = Image.open(out_dir / 'gui_image.png').convert('RGBA')

sa = np.array(saved)
ga = np.array(gui)
print('sizes', sa.shape, ga.shape)
diff = np.abs(sa.astype(int)-ga.astype(int))
print('max diff', diff.max(), 'mean', diff.mean())
maxpos = np.unravel_index(np.argmax(diff), diff.shape)
print('maxpos', maxpos)
print('saved pixel', sa[maxpos], 'gui pixel', ga[maxpos])

# write diff image
from PIL import Image
Image.fromarray((diff.clip(0,255)).astype('uint8')).save(out_dir / 'diff.png')
print('wrote', list(out_dir.iterdir()))
