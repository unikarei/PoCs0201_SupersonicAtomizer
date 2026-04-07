"""Tests for CLI full-run flow (P22-T02)."""

from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import LavalSweepResult, SimulationRunResult, StartupResult
from supersonic_atomizer.cli import (
    CLIOptions,
    format_laval_sweep_report,
    format_run_report,
    format_startup_report,
    main,
    parse_cli_args,
    run_cli,
)


class _StubApplicationService:
    """Minimal stub for application service boundary used in CLI tests."""

    def __init__(self) -> None:
        self.received_case_path: str | None = None
        self.startup_result = StartupResult(status="ready", case_path="unset")
        self.run_result: SimulationRunResult | None = None

    def run_startup(self, case_path: str) -> StartupResult:
        self.received_case_path = case_path
        if self.startup_result.case_path == "unset":
            return StartupResult(status="ready", case_path=case_path)
        return self.startup_result

    def run_simulation(self, case_path: str) -> SimulationRunResult:
        self.received_case_path = case_path
        if self.run_result is not None:
            return self.run_result
        return SimulationRunResult(status="completed", case_path=case_path)


class TestCLIFullRunArgParsing(unittest.TestCase):
    def test_default_mode_is_full_run(self) -> None:
        options = parse_cli_args(["case.yaml"])
        self.assertIsInstance(options, CLIOptions)
        self.assertEqual(options.command, "simulate")
        self.assertEqual(options.case_path, "case.yaml")
        self.assertFalse(options.startup_only)

    def test_startup_only_flag_preserved(self) -> None:
        options = parse_cli_args(["case.yaml", "--startup-only"])
        self.assertTrue(options.startup_only)

    def test_laval_sweep_mode_is_preserved(self) -> None:
        options = parse_cli_args(["laval-sweep", "examples/laval_nozzle_air.yaml"])

        self.assertEqual(options.command, "laval-sweep")
        self.assertEqual(options.case_path, "examples/laval_nozzle_air.yaml")


class TestCLIMainFullRun(unittest.TestCase):
    def test_main_without_startup_only_invokes_run_simulation(self) -> None:
        service = _StubApplicationService()

        result = main(["run-case.yaml"], application_service=service)

        self.assertIsInstance(result, SimulationRunResult)
        self.assertEqual(service.received_case_path, "run-case.yaml")
        self.assertEqual(result.status, "completed")

    def test_main_with_startup_only_invokes_run_startup(self) -> None:
        service = _StubApplicationService()

        result = main(["startup-case.yaml", "--startup-only"], application_service=service)

        self.assertIsInstance(result, StartupResult)
        self.assertEqual(service.received_case_path, "startup-case.yaml")
        self.assertEqual(result.status, "ready")

    def test_main_laval_sweep_invokes_runner(self) -> None:
        def _stub_sweep_runner(case_path: str, *, output_directory: str | None = None) -> LavalSweepResult:
            self.assertEqual(case_path, "examples/laval_nozzle_air.yaml")
            self.assertEqual(output_directory, "outputs/custom")
            return LavalSweepResult(
                case_path=case_path,
                plot_path="plot.png",
                summary_path="summary.json",
                report_path="report.md",
                curves=(),
                validation_status="pass",
                validation_observations=("ok",),
                notes=(),
            )

        result = main(
            ["laval-sweep", "examples/laval_nozzle_air.yaml", "--output-directory", "outputs/custom"],
            application_service=_StubApplicationService(),
            laval_sweep_runner=_stub_sweep_runner,
        )

        self.assertIsInstance(result, LavalSweepResult)


class TestFormatRunReport(unittest.TestCase):
    def test_completed_run_report(self) -> None:
        result = SimulationRunResult(status="completed", case_path="air.yaml")
        report = format_run_report(result)
        self.assertIn("Simulation completed", report)
        self.assertIn("air.yaml", report)

    def test_failed_run_report_with_stage(self) -> None:
        result = SimulationRunResult(
            status="failed",
            case_path="bad.yaml",
            failure_stage="startup",
            failure_message="missing file",
        )
        report = format_run_report(result)
        self.assertIn("Simulation failed", report)
        self.assertIn("startup", report)
        self.assertIn("missing file", report)

    def test_output_failed_report(self) -> None:
        result = SimulationRunResult(
            status="output-failed",
            case_path="case.yaml",
            failure_stage="outputs",
            failure_message="disk full",
        )
        report = format_run_report(result)
        self.assertIn("output failed", report)
        self.assertIn("disk full", report)

    def test_laval_sweep_report(self) -> None:
        result = LavalSweepResult(
            case_path="examples/laval_nozzle_air.yaml",
            plot_path="plot.png",
            summary_path="summary.json",
            report_path="report.md",
            curves=(),
            validation_status="pass",
            validation_observations=("ok",),
            notes=(),
        )
        report = format_laval_sweep_report(result)
        self.assertIn("Laval sweep completed", report)
        self.assertIn("report.md", report)


class TestRunCliFullRun(unittest.TestCase):
    def test_successful_full_run_writes_to_stdout_exit_0(self) -> None:
        service = _StubApplicationService()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = run_cli(
            ["case.yaml"],
            application_service=service,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Simulation completed", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_failed_full_run_writes_to_stderr_exit_1(self) -> None:
        service = _StubApplicationService()
        service.run_result = SimulationRunResult(
            status="failed",
            case_path="bad.yaml",
            failure_stage="simulation",
            failure_message="solver diverged",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = run_cli(
            ["bad.yaml"],
            application_service=service,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Simulation failed", stderr.getvalue())

    def test_startup_only_still_works_through_run_cli(self) -> None:
        service = _StubApplicationService()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = run_cli(
            ["case.yaml", "--startup-only"],
            application_service=service,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Startup ready", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
