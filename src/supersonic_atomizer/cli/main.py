"""Thin command-line entry for full MVP application execution."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import sys
from typing import TextIO
from typing import Sequence

from supersonic_atomizer.app import (
    ApplicationService,
    LavalSweepResult,
    SimulationRunResult,
    StartupResult,
    get_application_service,
    run_laval_sweep,
)
from supersonic_atomizer.gui.case_store import CaseStore, LegacyCaseMigrationResult


@dataclass(frozen=True, slots=True)
class CLIOptions:
    """Parsed CLI options for the current command boundary."""

    command: str
    case_path: str | None = None
    startup_only: bool = False
    output_directory: str | None = None
    cases_dir: str | None = None
    project_name: str | None = None
    dry_run: bool = False


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


def build_laval_sweep_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the Laval-nozzle back-pressure sweep command."""

    parser = argparse.ArgumentParser(
        prog="supersonic-atomizer laval-sweep",
        description="Run the Laval-nozzle internal x vs p/p0 back-pressure sweep.",
    )
    parser.add_argument("case_path", help="Path to the Laval-nozzle YAML case file.")
    parser.add_argument(
        "--output-directory",
        default=None,
        help="Optional output directory for sweep artifacts.",
    )
    return parser


def build_case_store_migration_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for migrating legacy flat GUI cases into a project."""

    parser = argparse.ArgumentParser(
        prog="supersonic-atomizer migrate-case-store",
        description="Move legacy flat cases/*.yaml files into cases/<project>/.",
    )
    parser.add_argument(
        "--cases-dir",
        default="cases",
        help="Root case-store directory to migrate. Defaults to cases/.",
    )
    parser.add_argument(
        "--project",
        default="default",
        help="Target project name for migrated legacy cases.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report which cases would be moved without writing changes.",
    )
    return parser


def parse_cli_args(argv: Sequence[str] | None = None) -> CLIOptions:
    """Parse CLI arguments into a small CLI options model."""

    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] == "laval-sweep":
        namespace = build_laval_sweep_parser().parse_args(args[1:])
        return CLIOptions(
            command="laval-sweep",
            case_path=namespace.case_path,
            output_directory=namespace.output_directory,
        )

    if args and args[0] == "migrate-case-store":
        namespace = build_case_store_migration_parser().parse_args(args[1:])
        return CLIOptions(
            command="migrate-case-store",
            cases_dir=namespace.cases_dir,
            project_name=namespace.project,
            dry_run=namespace.dry_run,
        )

    namespace = build_parser().parse_args(args)
    return CLIOptions(
        command="simulate",
        case_path=namespace.case_path,
        startup_only=namespace.startup_only,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    application_service: ApplicationService | None = None,
    laval_sweep_runner=run_laval_sweep,
) -> StartupResult | SimulationRunResult | LavalSweepResult | LegacyCaseMigrationResult:
    """Parse CLI inputs and hand off to the application service boundary."""

    options = parse_cli_args(argv)
    if options.command == "migrate-case-store":
        store = CaseStore(cases_dir=options.cases_dir)
        return store.migrate_legacy_cases(
            target_project=options.project_name,
            dry_run=options.dry_run,
        )

    if options.command == "laval-sweep":
        return laval_sweep_runner(options.case_path, output_directory=options.output_directory)

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


def format_laval_sweep_report(sweep_result: LavalSweepResult) -> str:
    """Format concise user-facing reporting for the Laval-nozzle sweep command."""

    return (
        "Laval sweep completed: "
        f"case={sweep_result.case_path}; "
        f"validation={sweep_result.validation_status}; "
        f"plot={sweep_result.plot_path}; "
        f"report={sweep_result.report_path}"
    )


def format_case_store_migration_report(result: LegacyCaseMigrationResult) -> str:
    """Format concise reporting for legacy case-store migration."""

    moved = ", ".join(result.moved_cases) if result.moved_cases else "none"
    skipped = ", ".join(result.skipped_cases) if result.skipped_cases else "none"
    action = "would move" if result.dry_run else "moved"
    return (
        f"Case-store migration {action} to project={result.target_project}; "
        f"moved={moved}; skipped={skipped}"
    )


def run_cli(
    argv: Sequence[str] | None = None,
    *,
    application_service: ApplicationService | None = None,
    laval_sweep_runner=run_laval_sweep,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI flow and write concise user-facing reporting."""

    result = main(
        argv,
        application_service=application_service,
        laval_sweep_runner=laval_sweep_runner,
    )

    if isinstance(result, LegacyCaseMigrationResult):
        (stdout or sys.stdout).write(format_case_store_migration_report(result) + "\n")
        return 0

    if isinstance(result, LavalSweepResult):
        (stdout or sys.stdout).write(format_laval_sweep_report(result) + "\n")
        return 0

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