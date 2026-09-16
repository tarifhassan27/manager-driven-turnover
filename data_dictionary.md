# Data Dictionary — Project 3 Synthetic Dataset

## employees.csv (2,500 rows)
| Column | Type | Description |
|---|---|---|
| employee_id | text | Unique employee identifier |
| manager_id | text | FK to managers.csv |
| grade | int (1-5) | 1 = junior ... 5 = principal/lead |
| hire_date | date | Staggered over a 5-year window ending 2026-09-01 |
| exit_date | date, nullable | Null if still employed at observation cutoff (censored) |
| tenure_days | int | Days from hire to exit, or hire to cutoff if censored |
| event_observed | int (0/1) | 1 = exited (event), 0 = still employed (right-censored) |

## managers.csv (180 rows)
| Column | Type | Description |
|---|---|---|
| manager_id | text | Unique manager identifier |
| team_size | int | Number of direct reports (5-25 range) |

## Observation cutoff
2026-09-01. Anyone still employed at this date is right-censored, not excluded.

## Modeling notes for Phase 3 (analysis)
- Survival time = `tenure_days`, event indicator = `event_observed` — standard
  right-censored survival data, ready for `lifelines.CoxPHFitter`.
- Candidate covariates: `manager_id` (as a random/frailty effect — consider
  `lifelines.CoxPHFitter` with a shared-frailty extension, or a fixed-effect
  dummy approach if frailty modeling isn't available; grid/model choice is a
  Phase 3 decision), `grade`, and `team_size` (join from managers.csv).
- Do NOT open `sealed_answer_key.json` before running and documenting the
  Phase 3 analysis. It exists only for the Phase 4 diff.
