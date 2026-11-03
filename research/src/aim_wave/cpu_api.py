"""Faithful research port of Wave's documented CPU/API harmonic candidate.

This is not Wave v3 (S fixed at one), nor the Activity/Qv candidate. The input
coordinates are A (CPU normalized by an explicit core reference) and P (the
documented API performance index). R and phi are their polar representation.
"""
from __future__ import annotations

import math
from typing import Any

MODEL_ID = "wave-cpu-api-harmonic-v0.1"


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def evaluate(observation: dict[str, Any], references: dict[str, float]) -> dict[str, Any]:
    """Calculate the documented CPU/API candidate without clipping or imputation.

    A = cpu_delta_seconds / (window_seconds * cpu_reference_cores)
    P = (Lmax / max(L, Lmax)) * (T / Tmax) * (1 - E/100)
    R = hypot(A, P); phi = atan2(P, A).

    `phi=0` at the zero vector follows the Wave README's stated convention;
    `phase_identifiable` makes explicit that this phase is not mathematically
    identifiable there. Missing API or CPU inputs produce partial results.
    """
    result: dict[str, Any] = {
        "model_id": MODEL_ID,
        "status": "invalid",
        "reason": None,
        "A_cpu_normalized": None,
        "cpu_percent_of_reference": None,
        "throughput_per_second": None,
        "requests_total": observation.get("requests_total"),
        "requests_failed": observation.get("requests_failed"),
        "error_percent": None,
        "latency_seconds": None,
        "P_api": None,
        "R": None,
        "phi_radians": None,
        "phase_identifiable": None,
        "wave_frequency_hz": None,
        "references": dict(references),
        "raw": dict(observation),
    }
    required_refs = ("cpu_reference_cores", "latency_reference_seconds", "throughput_reference_per_second")
    if any(not _finite(references.get(k)) or references[k] <= 0 for k in required_refs):
        result["reason"] = "invalid_reference"
        return result
    if "window_seconds" not in observation or not _finite(observation["window_seconds"]) or observation["window_seconds"] <= 0:
        result["reason"] = "invalid_window"
        return result

    dt = float(observation["window_seconds"])
    cpu_delta = observation.get("cpu_delta_seconds")
    cpu_valid = _finite(cpu_delta) and cpu_delta >= 0
    if cpu_delta is not None and not cpu_valid:
        result["reason"] = "invalid_cpu_delta"
        return result
    if cpu_valid:
        a = float(cpu_delta) / (dt * float(references["cpu_reference_cores"]))
        result["A_cpu_normalized"] = a
        result["cpu_percent_of_reference"] = 100.0 * a

    total = observation.get("requests_total")
    failed = observation.get("requests_failed")
    latency = observation.get("mean_latency_seconds")
    api_missing = total is None or failed is None or latency is None
    if not api_missing:
        if (not _finite(total) or not _finite(failed) or
                total < 0 or not 0 <= failed <= total):
            result["reason"] = "invalid_request_counts"
            return result
        if total == 0:
            api_missing = True
        elif not _finite(latency) or latency < 0:
            result["reason"] = "invalid_latency"
            return result
        else:
            throughput = total / dt
            error_percent = 100.0 * failed / total
            lref = float(references["latency_reference_seconds"])
            tref = float(references["throughput_reference_per_second"])
            p = (lref / max(float(latency), lref)) * (throughput / tref) * (1.0 - error_percent / 100.0)
            if not all(map(math.isfinite, (throughput, error_percent, p))):
                result["reason"] = "nonfinite_derived"
                return result
            result.update(throughput_per_second=throughput, error_percent=error_percent,
                          latency_seconds=float(latency), P_api=p)

    if not cpu_valid or api_missing:
        result.update(status="partial", reason="missing_cpu_or_api_input")
        return result

    a = result["A_cpu_normalized"]
    p = result["P_api"]
    r = math.hypot(a, p)
    phi = math.atan2(p, a) if r > 0 else 0.0
    result.update(status="ok", R=r, phi_radians=phi, phase_identifiable=(r > 0),
                  wave_frequency_hz=1.0)
    return result


def encode_wave(a: float, p: float, phase_fraction: float, frequency_hz: float = 1.0) -> float:
    """Evaluate the documented carrier y=A*cos(2*pi*f*t)+P*sin(2*pi*f*t)."""
    if not all(map(_finite, (a, p, phase_fraction, frequency_hz))) or frequency_hz <= 0:
        raise ValueError("finite coordinates/time and positive frequency required")
    t = float(phase_fraction)
    f = float(frequency_hz)
    return float(a) * math.cos(2 * math.pi * f * t) + float(p) * math.sin(2 * math.pi * f * t)
