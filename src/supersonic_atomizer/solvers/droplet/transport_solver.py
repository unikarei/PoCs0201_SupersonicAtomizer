"""Runtime droplet transport solver with optional breakup integration."""

from __future__ import annotations

from dataclasses import replace

from supersonic_atomizer.breakup import BreakupModel, BreakupModelInputs
from supersonic_atomizer.domain import DropletInjectionConfig, DropletSolution, DropletState, GasSolution
from supersonic_atomizer.solvers.droplet.diagnostics import (
    create_droplet_solver_diagnostics,
    raise_droplet_solver_failure,
    validate_droplet_state,
)
from supersonic_atomizer.solvers.droplet.drag_models import DragModel, StandardSphereDragModel
from supersonic_atomizer.solvers.droplet.updates import initialize_droplet_state, update_droplet_state


def _apply_breakup_model(
    *,
    gas_state,
    droplet_state: DropletState,
    breakup_model: BreakupModel,
) -> DropletState:
    """Apply the configured breakup model to the updated local droplet state."""

    decision = breakup_model.evaluate(
        BreakupModelInputs(
            gas_state=gas_state,
            droplet_state=droplet_state,
        )
    )
    final_state = replace(
        droplet_state,
        mean_diameter=decision.updated_mean_diameter,
        maximum_diameter=decision.updated_maximum_diameter,
        weber_number=decision.weber_number,
        breakup_triggered=decision.triggered,
    )
    validate_droplet_state(final_state)
    return final_state


def solve_droplet_transport(
    *,
    gas_solution: GasSolution,
    injection_config: DropletInjectionConfig,
    drag_model: DragModel | None = None,
    breakup_model: BreakupModel | None = None,
) -> DropletSolution:
    """Solve representative droplet transport aligned to the gas solution."""

    selected_drag_model = drag_model or StandardSphereDragModel()
    if not gas_solution.states:
        raise_droplet_solver_failure(
            category="State-consistency checks",
            message="Droplet transport requires a non-empty aligned gas solution.",
        )

    states: list[DropletState] = [
        initialize_droplet_state(
            gas_state=gas_solution.states[0],
            injection_config=injection_config,
            drag_model=selected_drag_model,
        )
    ]

    for index in range(1, len(gas_solution.states)):
        gas_state = gas_solution.states[index]
        dx_value = gas_solution.x_values[index] - gas_solution.x_values[index - 1]
        try:
            updated_state = update_droplet_state(
                previous_state=states[-1],
                gas_state=gas_state,
                dx_value=dx_value,
                drag_model=selected_drag_model,
            )
            if breakup_model is not None:
                updated_state = _apply_breakup_model(
                    gas_state=gas_state,
                    droplet_state=updated_state,
                    breakup_model=breakup_model,
                )
        except Exception as exc:
            raise_droplet_solver_failure(
                category="State-consistency checks" if breakup_model is None else "Transport/breakup checks",
                message=str(exc),
                failure_location=f"x={gas_state.x:.6f}",
                last_valid_state=states[-1],
            )
        states.append(updated_state)

    return DropletSolution(
        states=tuple(states),
        x_values=tuple(state.x for state in states),
        velocity_values=tuple(state.velocity for state in states),
        slip_velocity_values=tuple(state.slip_velocity for state in states),
        mean_diameter_values=tuple(state.mean_diameter for state in states),
        maximum_diameter_values=tuple(state.maximum_diameter for state in states),
        weber_number_values=tuple(state.weber_number for state in states),
        reynolds_number_values=tuple(state.reynolds_number for state in states),
        breakup_flags=tuple(state.breakup_triggered for state in states),
        diagnostics=create_droplet_solver_diagnostics(
            status="completed",
            messages=(
                "Droplet transport completed across all axial nodes."
                if breakup_model is None
                else "Droplet transport and breakup evaluation completed across all axial nodes."
            ,),
        ),
    )