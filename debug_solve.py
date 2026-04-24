from supersonic_atomizer.domain import BoundaryConditionConfig, GeometryConfig
from supersonic_atomizer.geometry import build_geometry_model
from supersonic_atomizer.solvers.gas import solve_quasi_1d_gas_flow
from supersonic_atomizer.thermo import AirThermoProvider
from supersonic_atomizer.common import NumericalError

geo = build_geometry_model(
    GeometryConfig(
        x_start=0.0,
        x_end=0.1,
        n_cells=2,
        area_definition={
            "type": "table",
            "x": [0.0, 0.05, 0.1],
            "A": [1.4e-4, 0.8e-4, 1.4e-4],
        },
    )
)

try:
    sol = solve_quasi_1d_gas_flow(
        geometry_model=geo,
        boundary_conditions=BoundaryConditionConfig(Pt_in=150000.0, Tt_in=320.0, Ps_out=100000.0),
        thermo_provider=AirThermoProvider(),
    )
    print("Solver returned solution with messages:", sol.diagnostics.messages)
except NumericalError as e:
    print("Solver raised NumericalError:", str(e))
except Exception as e:
    print("Solver raised other exception:", type(e), e)
