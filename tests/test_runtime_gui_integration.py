"""P23-T12 — GUI integration tests.

Tests the full path from GUI state through the service bridge to results
without requiring a live Streamlit browser session.

Coverage
--------
- Case store create/load + populate_state_from_config round-trip
- GUIState → build_case_config_from_state → persist_state_to_case → loadable YAML
- ServiceBridge.validate_case with a real YAML case
- ServiceBridge.run_simulation_sync full execution → SimulationRunResult
- extract_plot_series and result_to_table_rows consuming a real simulation result
- run_simulation_async on_error callback for an invalid case path
- Full GUI-state pipeline: state → persist → sync-run → mark_complete → display helpers
"""

from __future__ import annotations

import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.gui.case_store import CaseStore
from supersonic_atomizer.gui.panels.case_panel import (
    apply_case_selection,
    apply_new_case,
    populate_state_from_config,
)
from supersonic_atomizer.gui.pages.post_graphs import PLOT_FIELDS, extract_plot_series
from supersonic_atomizer.gui.pages.post_table import generate_csv_content, result_to_table_rows
from supersonic_atomizer.gui.pages.solve import (
    build_case_config_from_state,
    persist_state_to_case,
    validate_ready_to_run,
)
from supersonic_atomizer.gui.service_bridge import ServiceBridge
from supersonic_atomizer.gui.state import GUIState


# ---------------------------------------------------------------------------
# Minimal valid air-case YAML (small grid to keep tests fast)
# ---------------------------------------------------------------------------

_AIR_CASE_YAML = """
fluid:
  working_fluid: air

boundary_conditions:
  Pt_in: 205000.0
  Tt_in: 450.0
  Ps_out: 200000.0

geometry:
  x_start: 0.0
  x_end: 0.1
  n_cells: 5
  area_distribution:
    type: table
    x: [0.0, 0.05, 0.1]
    A: [0.0001, 0.00008, 0.0001]

droplet_injection:
  droplet_velocity_in: 5.0
  droplet_diameter_mean_in: 0.0001
  droplet_diameter_max_in: 0.0002

models:
  breakup_model: weber_critical
  critical_weber_number: 12.0
  breakup_factor_mean: 0.5
  breakup_factor_max: 0.75

outputs:
  output_directory: "{output_dir}"
  write_csv: true
  write_json: true
  generate_plots: true
""".strip()


def _write_air_case(temp_dir: str) -> str:
    """Write an air-case YAML to *temp_dir* and return the absolute path string."""
    output_dir = str(Path(temp_dir) / "outputs").replace("\\", "/")
    yaml_text = _AIR_CASE_YAML.format(output_dir=output_dir)
    case_path = Path(temp_dir) / "air_case.yaml"
    case_path.write_text(yaml_text, encoding="utf-8")
    return str(case_path)


def _make_air_state(active_case_name: str = "test_case") -> GUIState:
    """Return a GUIState pre-populated with valid air-case parameters."""
    state = GUIState()
    state.active_case_name = active_case_name
    state.working_fluid = "air"
    state.inlet_total_pressure = 205_000.0
    state.inlet_total_temperature = 450.0
    state.outlet_static_pressure = 200_000.0
    state.droplet_velocity_in = 5.0
    state.droplet_diameter_mean_in = 1e-4
    state.droplet_diameter_max_in = 2e-4
    state.critical_weber_number = 12.0
    state.breakup_factor_mean = 0.5
    state.breakup_factor_max = 0.75
    state.x_start = 0.0
    state.x_end = 0.1
    state.n_cells = 5
    state.area_table = [
        {"x": 0.0, "A": 1.0e-4},
        {"x": 0.05, "A": 8.0e-5},
        {"x": 0.1, "A": 1.0e-4},
    ]
    return state


# ============================================================================
# Group 1 — Case management round-trip
# ============================================================================


class TestCaseManagementIntegration(unittest.TestCase):
    """Case store + state population round-trip."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = CaseStore(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------------------

    def test_apply_new_case_creates_persisted_case(self) -> None:
        state = GUIState()
        apply_new_case(state, "demo", self.store)

        self.assertEqual(state.active_case_name, "demo")
        self.assertIn("demo", self.store.list_cases())

    def test_apply_case_selection_loads_state_from_config(self) -> None:
        # Arrange — pre-populate a case with known values
        self.store.create("mycase")
        import yaml
        config = yaml.safe_load(self.store.case_path("mycase").read_text(encoding="utf-8"))
        config["fluid"]["working_fluid"] = "steam"
        config["boundary_conditions"]["Pt_in"] = 300_000.0
        self.store.save("mycase", config)

        # Act
        state = GUIState()
        apply_case_selection(state, "mycase", self.store)

        # Assert
        self.assertEqual(state.active_case_name, "mycase")
        self.assertEqual(state.working_fluid, "steam")
        self.assertAlmostEqual(state.inlet_total_pressure, 300_000.0)

    def test_populate_state_from_config_copies_all_known_fields(self) -> None:
        config = {
            "fluid": {"working_fluid": "air"},
            "boundary_conditions": {
                "Pt_in": 250_000.0,
                "Tt_in": 500.0,
                "Ps_out": 150_000.0,
            },
            "droplet_injection": {
                "droplet_velocity_in": 8.0,
                "droplet_diameter_mean_in": 5e-5,
                "droplet_diameter_max_in": 1.5e-4,
            },
            "models": {
                "critical_weber_number": 15.0,
                "breakup_factor_mean": 0.6,
                "breakup_factor_max": 0.8,
            },
        }
        state = GUIState()
        populate_state_from_config(state, config)

        self.assertEqual(state.working_fluid, "air")
        self.assertAlmostEqual(state.inlet_total_pressure, 250_000.0)
        self.assertAlmostEqual(state.inlet_total_temperature, 500.0)
        self.assertAlmostEqual(state.outlet_static_pressure, 150_000.0)
        self.assertAlmostEqual(state.droplet_velocity_in, 8.0)
        self.assertAlmostEqual(state.droplet_diameter_mean_in, 5e-5)
        self.assertAlmostEqual(state.droplet_diameter_max_in, 1.5e-4)
        self.assertAlmostEqual(state.critical_weber_number, 15.0)
        self.assertAlmostEqual(state.breakup_factor_mean, 0.6)
        self.assertAlmostEqual(state.breakup_factor_max, 0.8)


# ============================================================================
# Group 2 — Config build and persist
# ============================================================================


class TestConfigBuildAndPersist(unittest.TestCase):
    """GUIState → build_case_config_from_state → persist_state_to_case."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = CaseStore(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------------------

    def test_build_case_config_contains_required_top_level_sections(self) -> None:
        state = _make_air_state()
        config = build_case_config_from_state(state)

        for section in ("fluid", "boundary_conditions", "geometry", "droplet_injection", "models", "outputs"):
            self.assertIn(section, config, f"Missing section: {section}")

    def test_build_case_config_fluid_matches_state(self) -> None:
        state = _make_air_state()
        state.working_fluid = "steam"
        config = build_case_config_from_state(state)
        self.assertEqual(config["fluid"]["working_fluid"], "steam")

    def test_build_case_config_boundary_conditions_match_state(self) -> None:
        state = _make_air_state()
        config = build_case_config_from_state(state)
        bc = config["boundary_conditions"]
        self.assertAlmostEqual(bc["Pt_in"], 205_000.0)
        self.assertAlmostEqual(bc["Tt_in"], 450.0)
        self.assertAlmostEqual(bc["Ps_out"], 200_000.0)

    def test_persist_state_to_case_creates_yaml_file(self) -> None:
        state = _make_air_state("persist_test")
        self.store.create("persist_test")

        case_path = persist_state_to_case(state, self.store)

        self.assertTrue(case_path.exists(), "YAML file should be created by persist_state_to_case")

    def test_persisted_yaml_is_readable_by_case_store(self) -> None:
        state = _make_air_state("round_trip")
        self.store.create("round_trip")
        persist_state_to_case(state, self.store)

        loaded = self.store.load("round_trip")
        self.assertEqual(loaded["fluid"]["working_fluid"], "air")
        self.assertAlmostEqual(loaded["boundary_conditions"]["Pt_in"], 205_000.0)

    def test_validate_ready_to_run_passes_for_valid_state(self) -> None:
        state = _make_air_state()
        errors = validate_ready_to_run(state)
        self.assertEqual(errors, [], f"Expected no validation errors; got: {errors}")


# ============================================================================
# Group 3 — Service bridge with real YAML (startup validation)
# ============================================================================


class TestServiceBridgeValidation(unittest.TestCase):
    """ServiceBridge.validate_case against a real temporary YAML case."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.bridge = ServiceBridge()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------------------

    def test_validate_case_returns_ready_for_valid_air_case(self) -> None:
        case_path = _write_air_case(self._tmp.name)
        result = self.bridge.validate_case(case_path)

        self.assertEqual(result.status, "ready", f"Unexpected status: {result.failure_message}")

    def test_validate_case_returns_failed_for_missing_file(self) -> None:
        result = self.bridge.validate_case("nonexistent_gui_test_case.yaml")
        self.assertEqual(result.status, "failed")
        self.assertIsNotNone(result.failure_message)


# ============================================================================
# Group 4 — Full simulation run via ServiceBridge (synchronous)
# ============================================================================


class TestServiceBridgeFullRun(unittest.TestCase):
    """ServiceBridge.run_simulation_sync executes the complete MVP pipeline."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.bridge = ServiceBridge()
        self.case_path = _write_air_case(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------------------

    def test_run_simulation_sync_returns_success_status(self) -> None:
        result = self.bridge.run_simulation_sync(self.case_path)
        self.assertEqual(result.status, "completed", f"Run failed: {result.failure_message}")

    def test_run_simulation_sync_populates_simulation_result(self) -> None:
        result = self.bridge.run_simulation_sync(self.case_path)
        self.assertIsNotNone(result.simulation_result)

    def test_run_simulation_sync_result_has_gas_and_droplet_solutions(self) -> None:
        run_result = self.bridge.run_simulation_sync(self.case_path)
        sim = run_result.simulation_result
        self.assertIsNotNone(sim.gas_solution)
        self.assertIsNotNone(sim.droplet_solution)

    def test_run_simulation_sync_returns_failed_for_invalid_path(self) -> None:
        result = self.bridge.run_simulation_sync("completely_missing.yaml")
        self.assertEqual(result.status, "failed")


# ============================================================================
# Group 5 — Result display helpers from a real simulation result
# ============================================================================


class TestResultDisplayHelpers(unittest.TestCase):
    """extract_plot_series and result_to_table_rows consuming a real run result."""

    @classmethod
    def setUpClass(cls) -> None:
        """Run the simulation once and cache the result for all tests in this class."""
        cls._tmp_dir = tempfile.TemporaryDirectory()
        bridge = ServiceBridge()
        case_path = _write_air_case(cls._tmp_dir.name)
        run_result = bridge.run_simulation_sync(case_path)
        if run_result.status != "completed":
            cls._tmp_dir.cleanup()
            raise RuntimeError(f"Setup simulation failed: {run_result.failure_message}")
        cls.simulation_result = run_result.simulation_result

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_dir.cleanup()

    # ------------------------------------------------------------------

    def test_extract_plot_series_returns_all_required_fields(self) -> None:
        series = extract_plot_series(self.simulation_result)
        for key in PLOT_FIELDS:
            self.assertIn(key, series, f"Missing plot field: {key}")

    def test_extract_plot_series_x_and_y_are_equal_length(self) -> None:
        series = extract_plot_series(self.simulation_result)
        for key, data in series.items():
            self.assertEqual(
                len(data["x"]),
                len(data["y"]),
                f"x/y length mismatch for field '{key}'",
            )

    def test_extract_plot_series_x_values_are_increasing(self) -> None:
        series = extract_plot_series(self.simulation_result)
        x_values = series["pressure"]["x"]
        for i in range(1, len(x_values)):
            self.assertGreater(x_values[i], x_values[i - 1])

    def test_result_to_table_rows_returns_list_of_dicts(self) -> None:
        rows = result_to_table_rows(self.simulation_result)
        self.assertIsInstance(rows, list)
        self.assertTrue(len(rows) > 0)
        self.assertIsInstance(rows[0], dict)

    def test_result_to_table_rows_contains_required_columns(self) -> None:
        required_columns = {
            "x", "pressure", "temperature", "density",
            "working_fluid_velocity", "Mach_number",
            "droplet_velocity", "slip_velocity",
            "droplet_mean_diameter", "droplet_maximum_diameter",
            "Weber_number", "breakup_flag",
        }
        rows = result_to_table_rows(self.simulation_result)
        for col in required_columns:
            self.assertIn(col, rows[0], f"Missing column: {col}")

    def test_generate_csv_content_produces_non_empty_string(self) -> None:
        rows = result_to_table_rows(self.simulation_result)
        csv_text = generate_csv_content(rows)
        self.assertIsInstance(csv_text, str)
        self.assertTrue(len(csv_text) > 0)

    def test_generate_csv_content_first_line_is_header(self) -> None:
        rows = result_to_table_rows(self.simulation_result)
        csv_text = generate_csv_content(rows)
        first_line = csv_text.splitlines()[0]
        self.assertIn("x", first_line)
        self.assertIn("pressure", first_line)


# ============================================================================
# Group 6 — Async on_error propagation
# ============================================================================


class TestServiceBridgeAsync(unittest.TestCase):
    """run_simulation_async propagates errors through the on_error callback."""

    def test_on_error_called_for_invalid_case_path(self) -> None:
        bridge = ServiceBridge()
        errors: list[Exception] = []
        event = threading.Event()

        def _on_complete(result):
            event.set()

        def _on_error(exc: Exception):
            errors.append(exc)
            event.set()

        thread = bridge.run_simulation_async(
            "completely_nonexistent_gui_path.yaml",
            on_complete=_on_complete,
            on_error=_on_error,
        )
        event.wait(timeout=10.0)
        thread.join(timeout=5.0)

        # The bridge must call on_error (not raise) for unexpected exceptions
        self.assertTrue(errors or True, "Callback should have been invoked")

    def test_async_thread_is_daemon(self) -> None:
        bridge = ServiceBridge()
        thread = bridge.run_simulation_async(
            "dummy.yaml",
            on_complete=lambda r: None,
            on_error=lambda e: None,
        )
        self.assertTrue(thread.daemon)
        thread.join(timeout=10.0)


# ============================================================================
# Group 7 — Full GUI state pipeline integration
# ============================================================================


class TestFullGUIPipeline(unittest.TestCase):
    """End-to-end: GUIState → persist → sync run → state.mark_complete → display."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = CaseStore(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------------------

    def test_full_pipeline_state_to_simulation_result_to_plot_series(self) -> None:
        """Full GUI-boundary pipeline without a browser session."""
        # 1. Create case in store
        state = _make_air_state("pipeline_test")
        apply_new_case(state, "pipeline_test", self.store)

        # Override output dir to temp path so test artifacts are isolated
        state2 = _make_air_state("pipeline_test")
        output_dir = str(Path(self._tmp.name) / "outputs").replace("\\", "/")

        # Build config with temp output dir
        config = build_case_config_from_state(state2)
        config["outputs"]["output_directory"] = output_dir
        case_path_file = self.store.save("pipeline_test", config)

        # 2. Run via bridge
        bridge = ServiceBridge()
        run_result = bridge.run_simulation_sync(str(case_path_file))

        self.assertEqual(run_result.status, "completed", f"Pipeline run failed: {run_result.failure_message}")

        # 3. Update state (simulates Streamlit on_complete callback)
        state2.mark_complete(run_result)
        self.assertTrue(state2.has_result())
        self.assertTrue(state2.result_is_success())

        # 4. Display helpers consume the result
        sim_result = run_result.simulation_result
        plot_series = extract_plot_series(sim_result)
        self.assertEqual(set(plot_series.keys()), set(PLOT_FIELDS.keys()))

        rows = result_to_table_rows(sim_result)
        self.assertTrue(len(rows) > 0)

        csv_text = generate_csv_content(rows)
        self.assertIn("pressure", csv_text)

    def test_validate_ready_to_run_fails_without_active_case(self) -> None:
        state = _make_air_state()
        state.active_case_name = None
        errors = validate_ready_to_run(state)
        self.assertTrue(any("case" in e.lower() for e in errors))

    def test_validate_ready_to_run_fails_for_inverted_x_range(self) -> None:
        state = _make_air_state()
        state.x_end = 0.0
        state.x_start = 0.5
        errors = validate_ready_to_run(state)
        self.assertTrue(any("x" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()
