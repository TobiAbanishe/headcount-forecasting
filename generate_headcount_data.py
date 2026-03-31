"""
generate_headcount_data.py
──────────────────────────────────────────────────────────────────────────────
Project 4: Headcount Forecasting | NorthBridge Financial (Simulated)
Author  : Oluwutobi Abanishe | github.com/TobiAbanishe
──────────────────────────────────────────────────────────────────────────────

Research Grounding
──────────────────
• SHRM (2023 Human Capital Benchmarking Report): Voluntary turnover in
  financial services averages 17.1%. Involuntary separations average 3.2%.
  Source: https://www.shrm.org/topics-tools/research/benchmarking

• LinkedIn Global Talent Trends (2023): Technology roles in financial
  services see attrition rates ~22–25% annually. 68% of CHROs in financial
  services identified workforce planning as a top-3 priority.
  Source: https://business.linkedin.com/talent-solutions/global-talent-trends

• LinkedIn Talent Insights (2023): Financial services firms are targeting
  5–8% annual headcount growth in Technology and Risk & Compliance functions
  driven by digital transformation and regulatory demands.

Outputs (saved to /data/)
─────────────────────────
  employees.csv         — Full employee master (all-time, including separated)
  headcount_monthly.csv — Monthly headcount snapshot by department
  separations.csv       — Individual separation events
  new_hires.csv         — Individual hire events
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# SEED
# ─────────────────────────────────────────────────────────────────────────────

np.random.seed(42)
random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Departments: base headcount as of Jan 2022, annual growth target, and
# voluntary attrition rate grounded in SHRM 2023 financial services benchmarks.
DEPARTMENTS = {
    "Retail Banking":    {"base_hc": 220, "annual_growth": 0.02, "vol_attrition": 0.17},
    "Corporate Banking": {"base_hc": 140, "annual_growth": 0.03, "vol_attrition": 0.14},
    "Risk & Compliance": {"base_hc": 130, "annual_growth": 0.05, "vol_attrition": 0.13},
    "Technology":        {"base_hc": 180, "annual_growth": 0.08, "vol_attrition": 0.22},
    "Operations":        {"base_hc": 175, "annual_growth": 0.01, "vol_attrition": 0.16},
    "Wealth Management": {"base_hc": 110, "annual_growth": 0.04, "vol_attrition": 0.15},
    "Human Resources":   {"base_hc":  45, "annual_growth": 0.02, "vol_attrition": 0.12},
}

JOB_LEVELS = ["Analyst", "Associate", "Manager", "Director/VP"]
LEVEL_DISTRIBUTION = [0.35, 0.35, 0.20, 0.10]  # realistic pyramid shape

# SHRM benchmark: junior roles (Analyst) turn over 2–3x faster than senior roles.
LEVEL_ATTRITION_MULTIPLIER = {
    "Analyst":    1.35,
    "Associate":  1.10,
    "Manager":    0.80,
    "Director/VP": 0.55,
}

LOCATIONS = ["Toronto", "Vancouver", "Calgary", "Montreal", "Lagos"]
LOCATION_WEIGHTS = [0.50, 0.18, 0.14, 0.13, 0.05]

# SHRM 2023: involuntary separations ~3.2%, retirement ~1% in financial services
INVOLUNTARY_RATE = 0.032
RETIREMENT_RATE = 0.010

START_DATE = date(2022, 1, 1)
END_DATE   = date(2024, 12, 31)
MONTHS     = pd.date_range(start=START_DATE, end=END_DATE, freq="MS")


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEE MASTER GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_hire_date_before_start(level: str) -> date:
    """
    Generate a realistic pre-simulation hire date based on typical tenure
    distributions for each job level (longer for senior roles).
    """
    mean_tenure_years = {"Analyst": 1.5, "Associate": 3.0, "Manager": 5.5, "Director/VP": 9.0}
    days_back = int(np.random.exponential(mean_tenure_years[level]) * 365)
    days_back = max(30, days_back)  # at least 30 days tenure before start
    return START_DATE - timedelta(days=days_back + random.randint(0, 180))


def generate_employee_master() -> tuple[pd.DataFrame, int]:
    """
    Build the initial active workforce as of Jan 2022 across all departments.
    Returns the employee DataFrame and the next available employee ID integer.
    """
    records = []
    emp_id = 1000

    for dept, config in DEPARTMENTS.items():
        for _ in range(config["base_hc"]):
            level = np.random.choice(JOB_LEVELS, p=LEVEL_DISTRIBUTION)
            records.append({
                "employee_id":     f"EMP{emp_id:04d}",
                "department":      dept,
                "job_level":       level,
                "location":        np.random.choice(LOCATIONS, p=LOCATION_WEIGHTS),
                "hire_date":       generate_hire_date_before_start(level),
                "status":          "Active",
                "separation_date": None,
                "separation_type": None,
            })
            emp_id += 1

    return pd.DataFrame(records), emp_id


# ─────────────────────────────────────────────────────────────────────────────
# MONTHLY SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def simulate_events(
    df_employees: pd.DataFrame, next_emp_id: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Simulate 36 months of headcount events:
      - Voluntary, involuntary, and retirement separations
      - Backfill hiring + growth hiring per department targets

    Returns: (all_employees_df, separations_df, new_hires_df, headcount_monthly_df)
    """
    separations    = []
    new_hires      = []
    hc_snapshots   = []
    emp_id_counter = next_emp_id

    workforce = df_employees.copy()

    for month_ts in MONTHS:
        month_date = month_ts.date()
        year       = month_date.year
        month_num  = month_date.month

        month_seps  = []
        month_hires = []

        active = workforce[workforce["status"] == "Active"]

        # ── STEP 1: SEPARATIONS ───────────────────────────────────────────────
        for dept, config in DEPARTMENTS.items():
            dept_active = active[active["department"] == dept]

            for idx, emp in dept_active.iterrows():
                vol_rate = (
                    config["vol_attrition"]
                    * LEVEL_ATTRITION_MULTIPLIER[emp["job_level"]]
                    / 12
                )
                inv_rate = INVOLUNTARY_RATE / 12
                ret_rate = RETIREMENT_RATE / 12

                roll = np.random.random()
                if roll < vol_rate:
                    sep_type = "Voluntary"
                elif roll < vol_rate + inv_rate:
                    sep_type = "Involuntary"
                elif roll < vol_rate + inv_rate + ret_rate:
                    sep_type = "Retirement"
                else:
                    continue

                workforce.at[idx, "status"]          = "Separated"
                workforce.at[idx, "separation_date"] = month_date
                workforce.at[idx, "separation_type"] = sep_type

                month_seps.append({
                    "employee_id":     emp["employee_id"],
                    "department":      dept,
                    "job_level":       emp["job_level"],
                    "location":        emp["location"],
                    "separation_date": month_date,
                    "separation_type": sep_type,
                    "year":            year,
                    "month":           month_num,
                })

        # ── STEP 2: NEW HIRES (backfill + growth) ────────────────────────────
        for dept, config in DEPARTMENTS.items():
            dept_seps_this_month = sum(
                1 for s in month_seps if s["department"] == dept
            )
            growth_hires = max(
                0, round(config["base_hc"] * config["annual_growth"] / 12)
            )
            total_hires = dept_seps_this_month + growth_hires

            for _ in range(total_hires):
                level    = np.random.choice(JOB_LEVELS, p=LEVEL_DISTRIBUTION)
                location = np.random.choice(LOCATIONS, p=LOCATION_WEIGHTS)
                new_id   = f"EMP{emp_id_counter:04d}"

                new_row = {
                    "employee_id":     new_id,
                    "department":      dept,
                    "job_level":       level,
                    "location":        location,
                    "hire_date":       month_date,
                    "status":          "Active",
                    "separation_date": None,
                    "separation_type": None,
                }
                workforce = pd.concat(
                    [workforce, pd.DataFrame([new_row])], ignore_index=True
                )
                month_hires.append({
                    "employee_id": new_id,
                    "department":  dept,
                    "job_level":   level,
                    "location":    location,
                    "hire_date":   month_date,
                    "year":        year,
                    "month":       month_num,
                })
                emp_id_counter += 1

        separations.extend(month_seps)
        new_hires.extend(month_hires)

        # ── STEP 3: HEADCOUNT SNAPSHOT ────────────────────────────────────────
        for dept in DEPARTMENTS:
            closing_hc = len(
                workforce[
                    (workforce["department"] == dept)
                    & (workforce["status"] == "Active")
                ]
            )
            hc_snapshots.append({
                "year":              year,
                "month":             month_num,
                "month_date":        month_date,
                "department":        dept,
                "closing_headcount": closing_hc,
                "new_hires":         sum(1 for h in month_hires if h["department"] == dept),
                "separations":       sum(1 for s in month_seps   if s["department"] == dept),
            })

    return (
        workforce,
        pd.DataFrame(separations),
        pd.DataFrame(new_hires),
        pd.DataFrame(hc_snapshots),
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    print("Step 1/3 — Generating employee master (Jan 2022 baseline)...")
    df_employees, next_id = generate_employee_master()
    print(f"          Baseline workforce: {len(df_employees):,} employees across "
          f"{df_employees['department'].nunique()} departments")

    print("Step 2/3 — Simulating 36 months of headcount events (Jan 2022 – Dec 2024)...")
    df_final, df_seps, df_hires, df_hc = simulate_events(df_employees, next_id)

    print("Step 3/3 — Saving outputs to /data/ ...")
    df_final.to_csv("data/employees.csv",          index=False)
    df_seps.to_csv("data/separations.csv",         index=False)
    df_hires.to_csv("data/new_hires.csv",          index=False)
    df_hc.to_csv("data/headcount_monthly.csv",     index=False)

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE — NorthBridge Financial")
    print("=" * 60)
    print(f"  All-time employees:       {len(df_final):,}")
    print(f"  Active at Dec 2024:       {len(df_final[df_final['status'] == 'Active']):,}")
    print(f"  Total separations:        {len(df_seps):,}")
    print(f"  Total new hires:          {len(df_hires):,}")
    print(f"  Headcount snapshots:      {len(df_hc):,} (36 months x 7 departments)")

    # Per-department closing headcount at end of simulation
    print("\n  Dec 2024 Headcount by Department:")
    dec_hc = df_hc[df_hc["month_date"] == date(2024, 12, 1)][
        ["department", "closing_headcount"]
    ].sort_values("closing_headcount", ascending=False)
    for _, row in dec_hc.iterrows():
        print(f"    {row['department']:<22} {row['closing_headcount']:>4}")
    print("=" * 60)
    print("\nFiles saved: employees.csv | separations.csv | new_hires.csv | headcount_monthly.csv")
