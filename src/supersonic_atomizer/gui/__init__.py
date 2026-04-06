"""Supersonic Atomizer GUI layer — Streamlit front-end.

This package contains the Streamlit-based graphical user interface.

Architectural boundary rules (docs/architecture.md, Appendix B.3):
- gui/ modules must depend only on app/services.py and result/domain models.
- gui/ modules must NOT import from solvers/, thermo/, config/, or breakup/ directly.
- service_bridge.py is the ONLY permitted call site into the application service.
- case_store.py owns ALL case-persistence logic; no other gui/ module reads/writes
  case files directly.
- Solver execution must remain non-blocking; use threading.Thread + st.session_state.
"""
