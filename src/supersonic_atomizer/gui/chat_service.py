"""Server-side LLM adapter for case-aware GUI chat (P34-T05)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from supersonic_atomizer.app.services import SimulationRunResult
from supersonic_atomizer.gui.job_store import get_job_store
from supersonic_atomizer.gui.multi_run import MultiRunSimulationResult


class ChatConfigurationError(RuntimeError):
    """Raised when no usable LLM provider configuration is available."""


@dataclass(frozen=True)
class ProviderConfig:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float


class ChatService:
    """Assemble case-aware prompts and call an OpenAI-compatible chat endpoint."""

    def _provider_config(self) -> ProviderConfig:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ChatConfigurationError(
                "LLM backend is not configured. Set OPENAI_API_KEY on the server to enable case chat."
            )
        return ProviderConfig(
            api_key=api_key,
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
            base_url=(os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip() or "https://api.openai.com/v1").rstrip("/"),
            timeout_seconds=float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "45")),
        )

    def generate_reply(
        self,
        *,
        project_name: str | None,
        case_name: str,
        case_config: dict[str, Any],
        messages: list[dict[str, str]],
    ) -> str:
        if not messages:
            raise ValueError("At least one user message is required.")
        provider = self._provider_config()
        prompt_messages = self._build_prompt_messages(
            project_name=project_name,
            case_name=case_name,
            case_config=case_config,
            messages=messages,
        )
        return self._call_provider(provider, prompt_messages)

    def _build_prompt_messages(
        self,
        *,
        project_name: str | None,
        case_name: str,
        case_config: dict[str, Any],
        messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        case_ref = case_name if not project_name else f"{project_name}/{case_name}"
        latest_summary = self._latest_result_summary(case_ref)
        system_prompt = (
            "You are an engineering assistant embedded in the Supersonic Atomizer GUI. "
            "Answer as a careful technical collaborator. Base your response on the selected case configuration and latest available solve summary. "
            "If the user asks for values that are not present, say so explicitly instead of inventing them. "
            "Keep answers concise but technically specific.\n\n"
            f"Selected case: {case_ref}\n"
            f"Case configuration JSON:\n{json.dumps(case_config, ensure_ascii=False, indent=2)}\n\n"
            f"Latest solve summary:\n{latest_summary}"
        )
        trimmed_messages: list[dict[str, str]] = []
        for message in messages[-20:]:
            role = message.get("role", "user")
            if role not in {"user", "assistant"}:
                continue
            trimmed_messages.append({"role": role, "content": str(message.get("content", ""))[:8000]})
        return [{"role": "system", "content": system_prompt}, *trimmed_messages]

    def _latest_result_summary(self, case_ref: str) -> str:
        record = get_job_store().latest_completed_for_case(case_ref)
        if record is None or record.result is None:
            return "No completed solve result is currently available for this case."

        result = record.result
        if isinstance(result, MultiRunSimulationResult):
            labeled = list(result.labeled_simulation_results())
            if not labeled:
                return f"Completed multi-run result recorded for {case_ref}, but no labeled runs were available."
            last_label, last_result = labeled[-1]
            sim_result = last_result
            return (
                f"Multi-run solve available with {result.run_count} runs. "
                f"Latest labeled run: {last_label}.\n{self._simulation_result_summary(sim_result)}"
            )

        if isinstance(result, SimulationRunResult) and result.simulation_result is not None:
            return self._simulation_result_summary(result.simulation_result)

        return f"Latest job for {case_ref} completed, but no structured simulation result summary was available."

    def _simulation_result_summary(self, simulation_result: Any) -> str:
        gas = simulation_result.gas_solution
        droplet = simulation_result.droplet_solution
        final_index = max(len(gas.x_values) - 1, 0)
        final_pressure = gas.pressure_values[final_index] if gas.pressure_values else None
        final_temperature = gas.temperature_values[final_index] if gas.temperature_values else None
        final_mach = gas.mach_number_values[final_index] if gas.mach_number_values else None
        final_velocity = gas.velocity_values[final_index] if gas.velocity_values else None
        final_area = gas.area_values[final_index] if gas.area_values else None
        final_droplet_velocity = droplet.velocity_values[final_index] if droplet.velocity_values else None
        final_mean_diameter = droplet.mean_diameter_values[final_index] if droplet.mean_diameter_values else None
        breakup_events = sum(1 for flag in droplet.breakup_flags if flag)

        # Small tabular snippet (first few axial points) with SI units to help
        # the assistant ground answers in concrete values without requiring
        # the full arrays. Limit to at most 5 rows for brevity.
        def _table_snippet(n: int = 5) -> str:
            rows = []
            headers = ["x [m]", "A [m^2]", "pressure [Pa]", "temperature [K]", "u [m/s]"]
            rows.append("\t".join(headers))
            count = min(n, len(gas.x_values))
            for i in range(count):
                x = gas.x_values[i]
                a = gas.area_values[i]
                p = gas.pressure_values[i]
                T = gas.temperature_values[i]
                u = gas.velocity_values[i]
                rows.append("\t".join(str(v) for v in (x, a, p, T, u)))
            return "\n".join(rows)

        return (
            f"Axial points: {len(gas.x_values)}\n"
            f"Final x [m]: {gas.x_values[final_index] if gas.x_values else 'n/a'}\n"
            f"Final area [m^2]: {final_area}\n"
            f"Final pressure [Pa]: {final_pressure}\n"
            f"Final temperature [K]: {final_temperature}\n"
            f"Final gas velocity [m/s]: {final_velocity}\n"
            f"Final Mach number [-]: {final_mach}\n"
            f"Final droplet velocity [m/s]: {final_droplet_velocity}\n"
            f"Final mean droplet diameter [m]: {final_mean_diameter}\n"
            f"Breakup events flagged: {breakup_events}\n\n"
            f"Tabular snippet (first rows):\n{_table_snippet(5)}"
        )

    def _call_provider(self, provider: ProviderConfig, messages: list[dict[str, str]]) -> str:
        payload = json.dumps(
            {
                "model": provider.model,
                "messages": messages,
                "temperature": 0.2,
            }
        ).encode("utf-8")
        req = request.Request(
            url=f"{provider.base_url}/chat/completions",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=provider.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc.reason}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response did not contain any choices.")
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            content = "\n".join(part for part in text_parts if part)
        content = str(content).strip()
        if not content:
            raise RuntimeError("LLM response content was empty.")
        return content
