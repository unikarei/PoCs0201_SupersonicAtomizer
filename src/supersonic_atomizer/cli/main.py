"""Thin command-line entry for full MVP application execution."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import sys
from typing import TextIO
from typing import Sequence

from supersonic_atomizer.app import (
    ApplicationService,
    SimulationRunResult,
    StartupResult,
    get_application_service,
)


@dataclass(frozen=True, slots=True)
class CLIOptions:
    """Parsed CLI options for the current command boundary."""

    case_path: str
    startup_only: bool = False


def build_parser() -> argparse.ArgumentParser:
    """Build the thin CLI parser without embedding runtime orchestration logic."""

    parser = argparse.ArgumentParser(
        prog="supersonic-atomizer",
        description="Run the Supersonic Atomizer simulation workflow.",
    )
    parser.add_argument("case_path", help="Path to the YAML case file.")
    parser.add_argument(
        "--startup-only",
        action="store_true",
        help="Run startup-stage dependency construction only.",
    )
    return parser


def parse_cli_args(argv: Sequence[str] | None = None) -> CLIOptions:
    """Parse CLI arguments into a small CLI options model."""

    namespace = build_parser().parse_args(argv)
    return CLIOptions(
        case_path=namespace.case_path,
        startup_only=namespace.startup_only,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    application_service: ApplicationService | None = None,
) -> StartupResult | SimulationRunResult:
    """Parse CLI inputs and hand off to the application service boundary."""

    options = parse_cli_args(argv)
    service = application_service or get_application_service()

    if options.startup_only:
        return service.run_startup(options.case_path)

    return service.run_simulation(options.case_path)


def format_startup_report(startup_result: StartupResult) -> str:
    """Format concise user-facing startup status for CLI reporting."""

    if startup_result.status == "ready":
        if startup_result.startup_dependencies is not None:
            return (
                "Startup ready: "
                f"case={startup_result.case_path}; "
                f"fluid={startup_result.startup_dependencies.case_config.fluid.working_fluid}; "
                f"thermo={startup_result.startup_dependencies.thermo_provider.provider_name}."
            )

        return f"Startup ready: case={startup_result.case_path}."

    if startup_result.failure_category == "InputParsingError":
        prefix = "Input error"
    elif startup_result.failure_category == "ConfigurationError":
        prefix = "Configuration error"
    elif startup_result.failure_category in {"ModelSelectionError", "ThermoError"}:
        prefix = "Startup dependency error"
    else:
        prefix = "Startup failure"

    return f"{prefix}: {startup_result.failure_message}"


def format_run_report(run_result: SimulationRunResult) -> str:
    """Format concise user-facing run status for CLI reporting."""

    if run_result.status == "completed":
        parts = [f"Simulation completed: case={run_result.case_path}"]

        if run_result.simulation_result is not None:
            parts.append(f"fluid={run_result.simulation_result.working_fluid}")
            if run_result.simulation_result.validation_report is not None:
                vr = run_result.simulation_result.validation_report
                parts.append(f"validation={vr.status} ({vr.checks_passed}/{vr.checks_run} passed)")
            if run_result.simulation_result.output_metadata is not None:
                parts.append(f"output_dir={run_result.simulation_result.output_metadata.output_directory}")

        return "; ".join(parts) + "."

    if run_result.status == "output-failed":
        return (
            f"Simulation ran but output failed: case={run_result.case_path}; "
            f"stage={run_result.failure_stage}; {run_result.failure_message}"
        )

    # Generic failure
    stage_info = f"; stage={run_result.failure_stage}" if run_result.failure_stage else ""
    return f"Simulation failed: case={run_result.case_path}{stage_info}; {run_result.failure_message}"


def run_cli(
    argv: Sequence[str] | None = None,
    *,
    application_service: ApplicationService | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI flow and write concise user-facing reporting."""

    result = main(argv, application_service=application_service)

    if isinstance(result, StartupResult):
        output = format_startup_report(result)
        if result.status == "ready":
            (stdout or sys.stdout).write(output + "\n")
            return 0
        (stderr or sys.stderr).write(output + "\n")
        return 1

    # SimulationRunResult
    output = format_run_report(result)
    if result.status == "completed":
        (stdout or sys.stdout).write(output + "\n")
        return 0
    (stderr or sys.stderr).write(output + "\n")
    return 1