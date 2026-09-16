"""
Project 3 — Manager-driven turnover, synthetic data generator.

Generates a synthetic employee roster with a Weibull-shaped baseline hazard
(time-since-hire drives risk directly, as in real turnover curves) plus three
independently-randomized covariate effects layered on top:
    - manager frailty (random effect per manager)
    - grade effect
    - team size effect

CRITICAL: this script draws its own random parameters from OS entropy at
runtime. It does NOT hardcode a fixed seed, and the realized parameter
values are written ONLY to sealed_answer_key.json. Nothing in this script,
its console output, or the generated CSVs reveals those values — the whole
point is that the analysis phase has no way to peek.

Do not open sealed_answer_key.json until Phase 4 (diff against seed).
"""

import numpy as np
import pandas as pd
import json
import secrets
from datetime import date, timedelta

# True random seed from OS entropy — not fixed, not knowable from this code
true_seed = secrets.randbits(32)
rng = np.random.default_rng(true_seed)

# ---------------------------------------------------------------------------
# Org structure
# ---------------------------------------------------------------------------
N_EMPLOYEES = 2500
N_MANAGERS = 180  # avg span of control ~13.9

# Team sizes: each manager gets a team size, employees assigned to fill it
team_sizes = rng.integers(5, 26, size=N_MANAGERS)
team_sizes = (team_sizes / team_sizes.sum() * N_EMPLOYEES).round().astype(int)
# adjust rounding to hit exact N_EMPLOYEES
diff = N_EMPLOYEES - team_sizes.sum()
team_sizes[: abs(diff)] += 1 if diff > 0 else -1

manager_ids = np.repeat(np.arange(N_MANAGERS), team_sizes)
rng.shuffle(manager_ids)
manager_ids = manager_ids[:N_EMPLOYEES]

# Grade: 1 (junior) to 5 (principal/lead), weighted toward junior/mid
grade_probs = [0.32, 0.30, 0.20, 0.12, 0.06]
grades = rng.choice([1, 2, 3, 4, 5], size=N_EMPLOYEES, p=grade_probs)

# Hire dates: staggered over a 5-year window ending at observation cutoff
OBS_CUTOFF = date(2026, 9, 1)
WINDOW_DAYS = 5 * 365
hire_offsets = rng.integers(0, WINDOW_DAYS, size=N_EMPLOYEES)
hire_dates = [OBS_CUTOFF - timedelta(days=int(d)) for d in hire_offsets]

# ---------------------------------------------------------------------------
# HIDDEN randomized effect sizes — not printed, not logged, sealed only
# ---------------------------------------------------------------------------
manager_frailty_sigma = rng.uniform(0.0, 0.75)          # 0 = managers don't matter at all
manager_frailty = rng.normal(0, manager_frailty_sigma, size=N_MANAGERS)

grade_beta = rng.uniform(-0.35, 0.35)                     # sign/size both hidden
team_size_beta = rng.uniform(-0.03, 0.03)                 # per-person effect, hidden

# Weibull baseline hazard shape (early-tenure risk elevated, standard pattern)
weibull_shape = rng.uniform(0.7, 1.1)     # <1 = declining hazard, common for tenure
weibull_scale_days = rng.uniform(1400, 2600)

team_size_std = (team_sizes[manager_ids] - team_sizes.mean()) / team_sizes.std()

linear_pred = (
    manager_frailty[manager_ids]
    + grade_beta * (grades - 3)          # centered on mid-grade
    + team_size_beta * (team_sizes[manager_ids] - team_sizes.mean())
)

# ---------------------------------------------------------------------------
# Simulate event times via inverse-CDF for Weibull proportional hazards
# ---------------------------------------------------------------------------
U = rng.uniform(1e-9, 1.0, size=N_EMPLOYEES)
survival_days = weibull_scale_days * (-np.log(U) * np.exp(-linear_pred)) ** (1 / weibull_shape)
survival_days = survival_days.round().astype(int)

rows = []
for i in range(N_EMPLOYEES):
    hire = hire_dates[i]
    days_to_cutoff = (OBS_CUTOFF - hire).days
    if survival_days[i] < days_to_cutoff:
        event_observed = 1
        exit_date = hire + timedelta(days=int(survival_days[i]))
        tenure_days = int(survival_days[i])
    else:
        event_observed = 0  # censored — still employed at cutoff
        exit_date = None
        tenure_days = days_to_cutoff
    rows.append({
        "employee_id": f"E{i:05d}",
        "manager_id": f"M{manager_ids[i]:04d}",
        "grade": int(grades[i]),
        "hire_date": hire.isoformat(),
        "exit_date": exit_date.isoformat() if exit_date else None,
        "tenure_days": tenure_days,
        "event_observed": event_observed,
    })

employees = pd.DataFrame(rows)

managers = pd.DataFrame({
    "manager_id": [f"M{i:04d}" for i in range(N_MANAGERS)],
    "team_size": team_sizes,
})

employees.to_csv("employees.csv", index=False)
managers.to_csv("managers.csv", index=False)

# Sealed answer key — do not open until Phase 4
sealed = {
    "true_seed": int(true_seed),
    "manager_frailty_sigma": float(manager_frailty_sigma),
    "grade_beta": float(grade_beta),
    "team_size_beta": float(team_size_beta),
    "weibull_shape": float(weibull_shape),
    "weibull_scale_days": float(weibull_scale_days),
    "manager_frailty_by_manager": {f"M{i:04d}": float(v) for i, v in enumerate(manager_frailty)},
}
with open("sealed_answer_key.json", "w") as f:
    json.dump(sealed, f, indent=2)

print("Generated:", len(employees), "employees,", len(managers), "managers.")
print("Files written: employees.csv, managers.csv, sealed_answer_key.json")
print("sealed_answer_key.json is SEALED — do not open until Phase 4.")
