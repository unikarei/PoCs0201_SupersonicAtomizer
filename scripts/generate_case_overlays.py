#!/usr/bin/env python3
"""Generate overlay PNGs for an outputs/<project>/<case> using existing run results.json files.

Usage: python scripts/generate_case_overlays.py <project> <case>
"""
from pathlib import Path
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PLOT_FIELDS = {
    'area_profile': 'A',
    'pressure': 'pressure',
    'temperature': 'temperature',
    'working_fluid_velocity': 'working_fluid_velocity',
    'droplet_velocity': 'droplet_velocity',
    'slip_velocity': 'slip_velocity',
    'Mach_number': 'Mach_number',
    'droplet_mean_diameter': 'droplet_mean_diameter',
    'droplet_maximum_diameter': 'droplet_maximum_diameter',
    'Weber_number': 'Weber_number',
    'pressure_over_total': 'pressure_over_total',
}

# Try to reuse the GUI's plot field metadata so titles and y-axis labels
# match the Graph tab. This import is best-effort — fall back to
# simple generated titles if the GUI module isn't available.
try:
    from supersonic_atomizer.gui.pages.post_graphs import PLOT_FIELDS as GUI_PLOT_FIELDS
except Exception:
    GUI_PLOT_FIELDS = None


def load_run_data(run_dir: Path):
    json_path = run_dir / 'results.json'
    if not json_path.is_file():
        return None
    try:
        d = json.loads(json_path.read_text(encoding='utf-8'))
    except Exception:
        return None
    numer = d.get('numerical_results', {})
    settings = d.get('settings_summary', {})
    return {'numerical_results': numer, 'settings': settings}


def make_label(settings):
    bc = settings.get('boundary_conditions', {}) if isinstance(settings, dict) else {}
    # prefer Ps_out then Pt_in
    if 'Ps_out' in bc:
        return f"Ps_out={int(bc['Ps_out'])}" if isinstance(bc['Ps_out'], (int,float)) else str(bc['Ps_out'])
    if 'Pt_in' in bc:
        return f"Pt_in={int(bc['Pt_in'])}" if isinstance(bc['Pt_in'], (int,float)) else str(bc['Pt_in'])
    return None


def generate_overlays(project: str, case: str):
    base = Path('outputs') / project / case
    if not base.is_dir():
        print('Case output directory not found:', base)
        return 2
    run_dirs = [p for p in sorted(base.iterdir()) if p.is_dir() and p.name.startswith('run-')]
    if not run_dirs:
        print('No run-* directories found under', base)
        return 1
    series_map = {k: [] for k in PLOT_FIELDS.keys()}
    # Build overlay_series structure compatible with GUI's extraction so
    # saved overlays match Graph tab rendering (titles, x_label, ylabel).
    overlay_series: dict[str, dict] = {}
    for run in run_dirs:
        data = load_run_data(run)
        if not data:
            continue
        numer = data['numerical_results']
        settings = data['settings']
        x = numer.get('x')
        if not x:
            continue
        label = make_label(settings) or run.name
        for plot_name, col in PLOT_FIELDS.items():
            y = numer.get(col)
            if y:
                series_map[plot_name].append((label, list(x), list(y)))
                # Build overlay_series entry
                entry = overlay_series.setdefault(plot_name, {
                    'title': (GUI_PLOT_FIELDS.get(plot_name)[0] if GUI_PLOT_FIELDS and plot_name in GUI_PLOT_FIELDS else plot_name.replace('_',' ')),
                    'x_label': 'x (m)',
                    'ylabel': (GUI_PLOT_FIELDS.get(plot_name)[2] if GUI_PLOT_FIELDS and plot_name in GUI_PLOT_FIELDS else ''),
                    'series': []
                })
                entry['series'].append({'label': label, 'x': list(x), 'y': list(y)})
    plots_dir = base / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for plot_name, series_list in series_map.items():
        if not series_list:
            continue
        # Prefer GUI-style title/labels when available
        gui_meta = overlay_series.get(plot_name)
        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        for label, xv, yv in series_list:
            ax.plot(xv, yv, label=label)
        ax.set_xlabel(gui_meta['x_label'] if gui_meta else 'x [m]')
        ax.set_ylabel(gui_meta['ylabel'] if gui_meta else plot_name)
        ax.set_title(gui_meta['title'] if gui_meta else plot_name.replace('_', ' '))
        ax.grid(True, alpha=0.3)
        if len(series_list) > 1:
            ax.legend(fontsize='small')
        fig.tight_layout()
        out_path = plots_dir / f"{plot_name}_overlay.png"
        fig.savefig(out_path)
        # Also write an alternate-capitalized filename so legacy GUI keys
        # (e.g. 'mach_number' -> 'Mach_number') can find a matching PNG.
        parts = plot_name.split("_", 1)
        if parts:
            alt_key = parts[0].capitalize() + ("_" + parts[1] if len(parts) > 1 else "")
            alt_path = plots_dir / f"{alt_key}_overlay.png"
            if not alt_path.exists():
                fig.savefig(alt_path)
        plt.close(fig)
        written[plot_name] = str(out_path)
    print('Wrote overlays for', project, case, '->', list(written.keys()))
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: generate_case_overlays.py <project> <case>')
        sys.exit(2)
    sys.exit(generate_overlays(sys.argv[1], sys.argv[2]))
