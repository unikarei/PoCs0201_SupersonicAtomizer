from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supersonic_atomizer.validation import (
    ValidationMetricTarget,
    documented_validation_case_registry,
    evaluate_validation_campaign,
    run_candidate_optimization,
    run_one_at_a_time_sensitivity,
    summarize_objective_uncertainty,
)


class TestRuntimeValidationQuantitativeWorkflow(unittest.TestCase):
    def test_documented_case_registry_points_to_existing_docs(self) -> None:
        registry = documented_validation_case_registry()

        self.assertIn("constant_area_gas_only", registry)
        self.assertIn("zero_or_near_zero_slip", registry)
        for doc_path in set(registry.values()):
            self.assertTrue(Path(doc_path).is_file())

    def test_evaluates_validation_campaign_baseline_objective(self) -> None:
        observed = {
            "constant_area_gas_only": {
                "exit_pressure_ratio": 0.951,
                "mean_mach": 0.241,
            },
            "zero_or_near_zero_slip": {
                "max_abs_slip": 3.0e-7,
            },
        }
        references = {
            "constant_area_gas_only": (
                ValidationMetricTarget("exit_pressure_ratio", 0.950, 0.01, weight=2.0),
                ValidationMetricTarget("mean_mach", 0.240, 0.01, weight=1.0),
            ),
            "zero_or_near_zero_slip": (
                ValidationMetricTarget("max_abs_slip", 0.0, 1.0e-6, weight=1.0),
            ),
        }

        report = evaluate_validation_campaign(
            observed_case_metrics=observed,
            reference_targets=references,
        )

        self.assertEqual(report.status, "pass")
        self.assertEqual(len(report.case_results), 2)
        self.assertGreaterEqual(report.baseline_objective, 0.0)
        self.assertTrue(any("baseline_objective=" in message for message in report.observations))

    def test_ranks_sensitivity_by_normalized_magnitude(self) -> None:
        baseline_parameters = {
            "critical_weber_number": 12.0,
            "two_way_feedback_relaxation": 0.35,
        }

        def objective(params: dict[str, float]) -> float:
            return (params["critical_weber_number"] - 10.0) ** 2 + 5.0 * params["two_way_feedback_relaxation"]

        sensitivity = run_one_at_a_time_sensitivity(
            baseline_parameters=baseline_parameters,
            perturbation_factors={
                "critical_weber_number": 1.1,
                "two_way_feedback_relaxation": 1.2,
            },
            objective_function=objective,
        )

        self.assertEqual(len(sensitivity), 2)
        self.assertGreaterEqual(
            abs(sensitivity[0].normalized_sensitivity),
            abs(sensitivity[1].normalized_sensitivity),
        )

    def test_selects_best_candidate_with_bounded_optimization(self) -> None:
        candidates = (
            {"critical_weber_number": 12.0, "breakup_factor_mean": 0.7},
            {"critical_weber_number": 10.0, "breakup_factor_mean": 0.6},
            {"critical_weber_number": 11.0, "breakup_factor_mean": 0.5},
        )

        def objective(params: dict[str, float]) -> float:
            return (params["critical_weber_number"] - 10.5) ** 2 + (params["breakup_factor_mean"] - 0.55) ** 2

        result = run_candidate_optimization(
            candidates=candidates,
            objective_function=objective,
        )

        self.assertEqual(result.evaluations, 3)
        self.assertEqual(result.best_parameters, {"critical_weber_number": 10.0, "breakup_factor_mean": 0.6})

    def test_summarizes_uncertainty_with_confidence_interval(self) -> None:
        summary = summarize_objective_uncertainty((1.0, 1.2, 0.8, 1.1, 0.9))

        self.assertEqual(summary.sample_count, 5)
        self.assertGreater(summary.objective_stddev, 0.0)
        self.assertLess(summary.ci95_lower, summary.objective_mean)
        self.assertGreater(summary.ci95_upper, summary.objective_mean)


if __name__ == "__main__":
    unittest.main()
