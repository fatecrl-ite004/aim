"""Faithful Python port of Wave's `s-fixed-reference-quality-v3` pipeline.

CPU/RSS are validated and preserved as covariates. They do not enter any v3
formula. Keep this model_id separate from the CPU/API harmonic candidate.
"""
from __future__ import annotations

import math
from typing import Any

from .cpu_api import _finite

MODEL_ID = "s-fixed-reference-quality-v3"
REFERENCES = {"S_reference": 1.0, "throughput_per_second": 40.0, "latency_seconds": 0.1}
BOUNDARY_RADIUS = math.sqrt(2 - math.sqrt(2))
BOUNDARY_ATOL = 1e-12


def canonicalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Map input field names to the exact Wave v3 observation contract."""
    return dict(
        service=raw["service"],
        window_index=raw.get("window_index", raw.get("window")),
        start_utc=raw.get("start_utc"),
        end_utc=raw.get("end_utc"),
        duration_seconds=raw.get("duration_seconds"),
        completed=raw.get("completed", raw.get("total_requests")),
        failed=raw.get("failed", raw.get("failed_requests")),
        latency_seconds=raw.get("mean_latency_seconds", raw.get("latency_seconds")),
        cpu_cores=raw.get("cpu_cores"),
        rss_bytes=raw.get("rss_bytes", raw.get("memory_rss_bytes")),
        counter_reset=raw.get("counter_reset", False),
    )


def derive(raw: dict[str, Any], source_kind: str, references: dict | None = None) -> dict[str, Any]:
    """Port Wave's v3 equations and states without changing their meanings."""
    ref = dict(REFERENCES if references is None else references)
    obs = canonicalize(raw)
    result = dict(model_id=MODEL_ID, source_kind=source_kind, **obs, reference=ref, raw=raw,
                  status="invalid", reason=None, operational_state="indeterminado",
                  S=None, P_raw=None, P=None, P_restricted=None, Q=None, D=None, theta=None,
                  alpha_raw=None, alpha=None, quality_factor=None, goodput_per_second=None,
                  clipping_applied=None, clipping_below_zero=None, clipping_above_one=None,
                  restriction_delta=None, boundary_radius=BOUNDARY_RADIUS,
                  boundary_delta=None, boundary_status="ausente")

    if (ref.get("S_reference") != 1.0 or not _finite(ref.get("S_reference")) or
            any(not _finite(ref.get(k)) or ref[k] <= 0 for k in ("throughput_per_second", "latency_seconds"))):
        result["reason"] = "invalid_reference"
        return result
    result["S"] = ref["S_reference"]
    wi = obs["window_index"]
    if not isinstance(wi, int) or isinstance(wi, bool) or wi < 0:
        result["reason"] = "invalid_window_index"
        return result
    if obs["counter_reset"]:
        result["reason"] = "counter_reset"
        return result
    dt, n, f, latency = (obs[k] for k in ("duration_seconds", "completed", "failed", "latency_seconds"))
    if not _finite(dt) or dt <= 0:
        result["reason"] = "invalid_duration"
        return result

    # CPU is a covariate in v3. Preserve it, but reject malformed supplied data.
    cpu = obs["cpu_cores"]
    if cpu is not None and (not _finite(cpu) or cpu < 0):
        result["reason"] = "invalid_cpu_cores"
        return result
    if n is None or f is None:
        result.update(status="missing", reason="missing_counts")
        return result
    if (not isinstance(n, int) or isinstance(n, bool) or not isinstance(f, int) or
            isinstance(f, bool) or not 0 <= f <= n):
        result["reason"] = "invalid_counts"
        return result
    if latency is not None and (not _finite(latency) or latency < 0):
        result["reason"] = "invalid_latency"
        return result

    goodput = (n - f) / dt
    if not math.isfinite(goodput):
        result["reason"] = "nonfinite_derived"
        return result
    result["goodput_per_second"] = goodput
    if n == 0:
        result.update(status="partial", reason="no_traffic", operational_state="ocioso")
        return result
    if latency is None:
        result.update(status="partial", reason="missing_latency")
        return result

    quality = ref["latency_seconds"] / max(latency, ref["latency_seconds"])
    raw_alpha = (goodput / ref["throughput_per_second"]) * quality
    if not math.isfinite(raw_alpha):
        result["reason"] = "nonfinite_derived"
        return result
    alpha = min(1.0, max(0.0, raw_alpha))
    p = alpha
    q = math.sqrt(1.0 - p) * math.sqrt(1.0 + p)
    d = math.hypot(p - 1.0, q)
    theta = math.atan2(q, p)
    delta = d - BOUNDARY_RADIUS
    boundary_status = "fronteira" if abs(delta) <= BOUNDARY_ATOL else ("dentro" if delta < 0 else "fora")
    result.update(status="ok", reason=None, operational_state="observado", S=1.0,
                  P_raw=raw_alpha, P=p, P_restricted=p, Q=q, D=d, theta=theta,
                  alpha_raw=raw_alpha, alpha=alpha, quality_factor=quality,
                  clipping_below_zero=raw_alpha < 0, clipping_above_one=raw_alpha > 1,
                  clipping_applied=raw_alpha != alpha, restriction_delta=p - raw_alpha,
                  boundary_delta=delta, boundary_status=boundary_status)
    return result
