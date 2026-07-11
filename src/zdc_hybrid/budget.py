from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobEstimate:
    name: str
    hourly_usd: float
    maximum_hours: float
    replicas: int = 1

    @property
    def maximum_usd(self) -> float:
        return self.hourly_usd * self.maximum_hours * self.replicas


def assert_planned_budget(
    jobs: list[JobEstimate],
    *,
    planned_limit_usd: float = 78.0,
    absolute_credit_limit_usd: float = 90.0,
) -> float:
    if planned_limit_usd > absolute_credit_limit_usd:
        raise ValueError("planned limit exceeds the absolute credit limit")
    invalid = (
        job.hourly_usd < 0 or job.maximum_hours <= 0 or job.replicas != 1 for job in jobs
    )
    if any(invalid):
        raise ValueError(
            "jobs require nonnegative rates, positive timeouts, and exactly one replica"
        )
    total = sum(job.maximum_usd for job in jobs)
    if total > planned_limit_usd + 1e-12:
        raise ValueError(f"planned maximum ${total:.2f} exceeds ${planned_limit_usd:.2f}")
    return total
