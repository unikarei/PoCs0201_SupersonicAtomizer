"""Runtime droplet transport solver with optional breakup integration."""

from __future__ import annotations

from dataclasses import replace

from supersonic_atomizer.breakup import BreakupModel, BreakupModelInputs
from supersonic_atomizer.domain import CouplingSourceTerms, DropletInjectionConfig, DropletSolution, DropletState, GasSolution
from supersonic_atomizer.solvers.droplet.diagnostics import (
    create_droplet_solver_diagnostics,
    raise_droplet_solver_failure,
    validate_droplet_state,
)
from supersonic_atomizer.solvers.droplet.drag_models import DragModel, StandardSphereDragModel
from supersonic_atomizer.solvers.droplet.updates import (
    compute_distribution_moments,
    initialize_droplet_state,
    update_droplet_state,
)


def _apply_breakup_model(
    *,
    gas_state,
    droplet_state: DropletState,
    breakup_model: BreakupModel,
    dt: float | None = None,
) -> DropletState:
    """Apply the configured breakup model to the updated local droplet state."""

    decision = breakup_model.evaluate(
        BreakupModelInputs(
            gas_state=gas_state,
            droplet_state=droplet_state,
            dt=dt,
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


def _extract_coupling_source_terms(
    *,
    gas_solution: GasSolution,
    droplet_states: tuple[DropletState, ...],
    water_mass_flow_rate: float | None,
) -> CouplingSourceTerms:
    """Estimate aligned liquid-to-gas source terms from droplet acceleration history."""

    state_count = len(droplet_states)
    if water_mass_flow_rate is None or water_mass_flow_rate <= 0.0:
        return CouplingSourceTerms(
            mass_source_values=tuple(0.0 for _ in range(state_count)),
            momentum_source_values=tuple(0.0 for _ in range(state_count)),
            energy_source_values=tuple(0.0 for _ in range(state_count)),
        )

    mass_sources: list[float] = [0.0]
    momentum_sources: list[float] = [0.0]
    energy_sources: list[float] = [0.0]

    for index in range(1, state_count):
        dx_value = gas_solution.x_values[index] - gas_solution.x_values[index - 1]
        transport_velocity = max(abs(gas_solution.velocity_values[index]), 1.0e-9)
        dt_value = max(dx_value / transport_velocity, 1.0e-12)
        droplet_acceleration = (
            droplet_states[index].velocity - droplet_states[index - 1].velocity
        ) / dt_value
        control_volume_area = max(gas_solution.area_values[index], 1.0e-12)

        momentum_source = -(water_mass_flow_rate * droplet_acceleration) / control_volume_area
        mean_droplet_velocity = 0.5 * (
            droplet_states[index].velocity + droplet_states[index - 1].velocity
        )
        energy_source = momentum_source * mean_droplet_velocity

        mass_sources.append(0.0)
        momentum_sources.append(momentum_source)
        energy_sources.append(energy_source)

    return CouplingSourceTerms(
        mass_source_values=tuple(mass_sources),
        momentum_source_values=tuple(momentum_sources),
        energy_source_values=tuple(energy_sources),
    )


def solve_droplet_transport(
    *,
    gas_solution: GasSolution,
    injection_config: DropletInjectionConfig,
    drag_model: DragModel | None = None,
    breakup_model: BreakupModel | None = None,
    distribution_model: str = "mono",
    distribution_sigma: float = 0.35,
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
            distribution_model=distribution_model,
            distribution_sigma=distribution_sigma,
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
                distribution_model=distribution_model,
                distribution_sigma=distribution_sigma,
            )
            if breakup_model is not None:
                # Compute a local dt estimate mapping axial dx -> time using
                # local gas velocity as transport velocity. Guard against
                # zero velocities with a small floor value.
                transport_velocity = max(abs(gas_state.velocity), 1.0e-9)
                dt_value = max(dx_value / transport_velocity, 1.0e-12)
                updated_state = _apply_breakup_model(
                    gas_state=gas_state,
                    droplet_state=updated_state,
                    breakup_model=breakup_model,
                    dt=dt_value,
                )
                smd_diameter, diameter_stddev = compute_distribution_moments(
                    mean_diameter=updated_state.mean_diameter,
                    maximum_diameter=updated_state.maximum_diameter,
                    distribution_model=distribution_model,
                    distribution_sigma=distribution_sigma,
                )
                updated_state = replace(
                    updated_state,
                    smd_diameter=smd_diameter,
                    diameter_stddev=diameter_stddev,
                )
        except Exception as exc:
            raise_droplet_solver_failure(
                category="State-consistency checks" if breakup_model is None else "Transport/breakup checks",
                message=str(exc),
                failure_location=f"x={gas_state.x:.6f}",
                last_valid_state=states[-1],
            )
        states.append(updated_state)

    aligned_states = tuple(states)
    coupling_source_terms = _extract_coupling_source_terms(
        gas_solution=gas_solution,
        droplet_states=aligned_states,
        water_mass_flow_rate=injection_config.water_mass_flow_rate,
    )

    return DropletSolution(
        states=aligned_states,
        x_values=tuple(state.x for state in aligned_states),
        velocity_values=tuple(state.velocity for state in aligned_states),
        slip_velocity_values=tuple(state.slip_velocity for state in aligned_states),
        mean_diameter_values=tuple(state.mean_diameter for state in aligned_states),
        maximum_diameter_values=tuple(state.maximum_diameter for state in aligned_states),
        weber_number_values=tuple(state.weber_number for state in aligned_states),
        reynolds_number_values=tuple(state.reynolds_number for state in aligned_states),
        breakup_flags=tuple(state.breakup_triggered for state in aligned_states),
        smd_diameter_values=tuple(state.smd_diameter for state in aligned_states),
        diameter_stddev_values=tuple(state.diameter_stddev for state in aligned_states),
        coupling_source_terms=coupling_source_terms,
        diagnostics=create_droplet_solver_diagnostics(
            status="completed",
            messages=(
                "Droplet transport completed across all axial nodes."
                if breakup_model is None
                else "Droplet transport and breakup evaluation completed across all axial nodes.",
                f"distribution_model={distribution_model}",
                "coupling_sources=estimated",
            ),
        ),
    )