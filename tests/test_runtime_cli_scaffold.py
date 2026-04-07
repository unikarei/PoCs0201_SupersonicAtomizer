from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import LavalSweepResult, SimulationRunResult, StartupResult
from supersonic_atomizer.cli import (
    CLIOptions,
    build_laval_sweep_parser,
    build_parser,
    format_laval_sweep_report,
    format_startup_report,
    main,
    parse_cli_args,
    run_cli,
)


class _StubApplicationService:
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


class TestRuntimeCliScaffold(unittest.TestCase):
    def test_parse_cli_args_returns_case_path_and_basic_run_option(self) -> None:
        options = parse_cli_args(["example-case.yaml", "--startup-only"])

        self.assertIsInstance(options, CLIOptions)
        self.assertEqual(options.command, "simulate")
        self.assertEqual(options.case_path, "example-case.yaml")
        self.assertTrue(options.startup_only)

    def test_parse_cli_args_supports_laval_sweep_command(self) -> None:
        options = parse_cli_args([
            "laval-sweep",
            "examples/laval_nozzle_air.yaml",
            "--output-directory",
            "outputs/sweep",
        ])

        self.assertEqual(options.command, "laval-sweep")
        self.assertEqual(options.case_path, "examples/laval_nozzle_air.yaml")
        self.assertEqual(options.output_directory, "outputs/sweep")

    def test_build_parser_accepts_required_case_path_argument(self) -> None:
        parser = build_parser()

        namespace = parser.parse_args(["sample-case.yaml"])

        self.assertEqual(namespace.case_path, "sample-case.yaml")
        self.assertFalse(namespace.startup_only)

    def test_build_laval_sweep_parser_accepts_optional_output_directory(self) -> None:
        parser = build_laval_sweep_parser()

        namespace = parser.parse_args(["examples/laval_nozzle_air.yaml", "--output-directory", "outputs/custom"])

        self.assertEqual(namespace.case_path, "examples/laval_nozzle_air.yaml")
        self.assertEqual(namespace.output_directory, "outputs/custom")

    def test_main_hands_case_path_to_application_service_boundary(self) -> None:
        application_service = _StubApplicationService()

        result = main(
            ["startup-case.yaml", "--startup-only"],
            application_service=application_service,
        )

        self.assertEqual(application_service.received_case_path, "startup-case.yaml")
        self.assertIsInstance(result, StartupResult)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.case_path, "startup-case.yaml")

    def test_format_startup_report_distinguishes_configuration_failures(self) -> None:
        startup_result = StartupResult(
            status="failed",
            case_path="bad-case.yaml",
            failure_category="ConfigurationError",
            failure_message="geometry is invalid",
        )

        report = format_startup_report(startup_result)

        self.assertEqual(report, "Configuration error: geometry is invalid")

    def test_format_laval_sweep_report_includes_validation_and_paths(self) -> None:
        sweep_result = LavalSweepResult(
            case_path="examples/laval_nozzle_air.yaml",
            plot_path="outputs/plot.png",
            summary_path="outputs/summary.json",
            report_path="outputs/report.md",
            curves=(),
            validation_status="pass",
            validation_observations=("ok",),
            notes=(),
        )

        report = format_laval_sweep_report(sweep_result)

        self.assertIn("Laval sweep completed", report)
        self.assertIn("validation=pass", report)
        self.assertIn("outputs/report.md", report)

    def test_run_cli_writes_ready_status_to_stdout(self) -> None:
        application_service = _StubApplicationService()
        application_service.startup_result = StartupResult(
            status="ready",
            case_path="ok-case.yaml",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = run_cli(
            ["ok-case.yaml", "--startup-only"],
            application_service=application_service,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Startup ready:", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_run_cli_supports_laval_sweep_command(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        def _stub_sweep_runner(case_path: str, *, output_directory: str | None = None) -> LavalSweepResult:
            self.assertEqual(case_path, "examples/laval_nozzle_air.yaml")
            self.assertEqual(output_directory, "outputs/sweep")
            return LavalSweepResult(
                case_path=case_path,
                plot_path="outputs/sweep/plot.png",
                summary_path="outputs/sweep/summary.json",
                report_path="outputs/sweep/report.md",
                curves=(),
                validation_status="pass",
                validation_observations=("ok",),
                notes=(),
            )

        exit_code = run_cli(
            ["laval-sweep", "examples/laval_nozzle_air.yaml", "--output-directory", "outputs/sweep"],
            stdout=stdout,
            stderr=stderr,
            application_service=_StubApplicationService(),
            laval_sweep_runner=_stub_sweep_runner,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Laval sweep completed", stdout.getvalue())

    def test_run_cli_writes_dependency_failure_to_stderr(self) -> None:
        application_service = _StubApplicationService()
        application_service.startup_result = StartupResult(
            status="failed",
            case_path="steam-case.yaml",
            failure_category="ModelSelectionError",
            failure_message="steam backend is unavailable",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = run_cli(
            ["steam-case.yaml", "--startup-only"],
            application_service=application_service,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(),
            "Startup dependency error: steam backend is unavailable\n",
        )


if __name__ == "__main__":
    unittest.main()