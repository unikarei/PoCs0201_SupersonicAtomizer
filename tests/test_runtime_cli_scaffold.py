from pathlib import Path
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.app import SimulationRunResult, StartupResult
from supersonic_atomizer.cli import (
    CLIOptions,
    build_parser,
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
        self.assertEqual(options.case_path, "example-case.yaml")
        self.assertTrue(options.startup_only)

    def test_build_parser_accepts_required_case_path_argument(self) -> None:
        parser = build_parser()

        namespace = parser.parse_args(["sample-case.yaml"])

        self.assertEqual(namespace.case_path, "sample-case.yaml")
        self.assertFalse(namespace.startup_only)

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