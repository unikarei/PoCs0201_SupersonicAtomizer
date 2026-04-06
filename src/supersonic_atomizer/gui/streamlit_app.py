"""Streamlit script entry point for the GUI launcher.

This tiny wrapper exists because `streamlit run` expects a Python script path.
The real GUI composition remains in `gui/app.py`.
"""

from supersonic_atomizer.gui.app import run_gui


run_gui()
