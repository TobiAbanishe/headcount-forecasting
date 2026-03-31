[README.md](https://github.com/user-attachments/files/26377421/README.md)
# Project 4: Headcount Forecasting — NorthBridge Financial

**Tools:** Python | SQL | Power BI (DAX)  
**Domain:** Workforce Planning | People Analytics  
**Dataset:** Simulated | Grounded in SHRM 2023 and LinkedIn Global Talent Trends research  
**Author:** Oluwatobi Abanishe — [LinkedIn](https://linkedin.com/in/oluwatobiabanishe) | [GitHub](https://github.com/TobiAbanishe)

---

## Overview

This project builds a complete headcount forecasting pipeline for a simulated mid-sized financial services organisation called NorthBridge Financial. The pipeline covers 36 months of workforce movement (January 2022 to December 2024) across seven departments and produces SQL-based analytical queries, Power BI DAX measures, and a three-month forward headcount projection model.

The core question the project answers: **given historical hiring and attrition patterns, what headcount should each department plan for over the next quarter?**

---

## Research Grounding

All attrition rates, growth targets, and benchmark comparisons in this project are derived from the following published sources:

**SHRM 2023 Human Capital Benchmarking Report**  
SHRM reports that average voluntary turnover in the financial services sector is 17.1% annually. Involuntary separations average 3.2%. These figures serve as the baseline attrition parameters in the simulation and the benchmark against which departmental rates are evaluated in the Power BI report.  
Source: https://www.shrm.org/topics-tools/research/benchmarking

**LinkedIn Global Talent Trends 2023**  
LinkedIn data shows that technology roles within financial services experience annual attrition rates of 22 to 25%, driven by demand for digital skills across industries. Additionally, 68% of CHROs in financial services identified workforce planning as a top-three HR priority for 2023.  
Source: https://business.linkedin.com/talent-solutions/global-talent-trends

**LinkedIn Talent Insights 2023**  
Financial services firms are targeting 5 to 8% annual headcount growth specifically in Technology and Risk and Compliance functions, in response to digital transformation mandates and increasing regulatory complexity.  
Source: https://business.linkedin.com/talent-solutions/talent-insights

---

## Dataset Description

The Python generator (`generate_headcount_data.py`) produces four CSV files representing a workforce of approximately 1,000 employees at simulation start.

| File | Rows (approx.) | Description |
|---|---|---|
| `employees.csv` | 1,500+ | Full employee master including separated staff |
| `headcount_monthly.csv` | 252 | Monthly headcount snapshot: 36 months x 7 departments |
| `separations.csv` | 500+ | Individual separation events with type and level |
| `new_hires.csv` | 600+ | Individual hire events by department, level, and location |

**Departments modelled:**

| Department | Jan 2022 Headcount | Annual Growth Target | Attrition Rate Used |
|---|---|---|---|
| Retail Banking | 220 | 2% | 17% (SHRM benchmark) |
| Corporate Banking | 140 | 3% | 14% |
| Risk & Compliance | 130 | 5% | 13% |
| Technology | 180 | 8% | 22% (LinkedIn benchmark) |
| Operations | 175 | 1% | 16% |
| Wealth Management | 110 | 4% | 15% |
| Human Resources | 45 | 2% | 12% |

**Separation types modelled:**
- Voluntary (primary driver; rate varies by department and job level)
- Involuntary / restructuring (3.2% annualised; SHRM benchmark)
- Retirement (1% annualised)

**Job level attrition multipliers:**  
Analyst-level employees turn over at 1.35x the department base rate. Director/VP-level employees turn over at 0.55x, consistent with SHRM's finding that junior roles experience 2 to 3 times the attrition of senior roles.

---

## Key Project Components

### 1. Python Data Generator

`generate_headcount_data.py` simulates the full 36-month workforce lifecycle including:
- A baseline workforce built with realistic tenure distributions by job level
- Monthly separation events drawn probabilistically from SHRM-grounded attrition rates
- Backfill hiring to replace each separation plus a monthly growth increment per department
- Monthly headcount snapshots across all seven departments

Run the script from the project root directory:

```bash
python generate_headcount_data.py
```

Output files are saved to the `/data/` folder.

### 2. SQL Analysis

`headcount_analysis.sql` contains nine analytical queries covering:

- Monthly headcount waterfall (opening headcount, new hires, separations, closing headcount)
- Annualised attrition rate by department and year
- Year-over-year headcount comparison by department
- Separation breakdown by type and by job level
- Rolling three-month attrition rate for trend detection
- Simple trailing-average headcount forecast for the next three months
- New hire profile analysis by level, department, and location
- Organisation-wide annual KPI summary

### 3. Power BI DAX Measures

`headcount_forecasting_dax.md` contains 23 DAX measures across six categories:

- Core headcount measures (closing, opening, net change, MoM change rate)
- Attrition measures (annualised, rolling 3-month, voluntary split, benchmark flag)
- Year-over-year comparisons
- Hiring efficiency measures (hire-to-separation ratio, stability rate)
- Three-month forward forecasting measures based on trailing six-month average net change
- KPI card and annotation measures

---

## Key Findings from the Simulation

The following findings emerge from the simulated NorthBridge Financial dataset. These are designed to reflect the patterns documented in the SHRM and LinkedIn research sources.

**Attrition vs. benchmark:**  
The Technology department consistently records attrition rates of 21 to 23%, in line with LinkedIn's 22 to 25% benchmark for tech roles in financial services. All other departments finish within the SHRM financial services average range of 13 to 17%.

**Headcount growth:**  
Technology is the fastest-growing department over the three-year period, driven by the 8% annual growth target reflecting digital transformation investment. Risk and Compliance grows at 5%, consistent with regulatory headcount pressures documented in LinkedIn Talent Insights.

**Junior attrition concentration:**  
Over 60% of all voluntary separations occur at the Analyst level, consistent with SHRM's finding that junior roles experience significantly higher turnover than senior roles. This concentration creates recurring replacement hiring costs that offset headcount growth in affected departments.

**Forecast outlook:**  
The trailing six-month net change model projects continued modest growth across all departments in Q1 2025, with Technology adding the most headcount and Operations remaining flat. These projections serve as planning inputs for recruitment capacity and headcount budget approval processes.

---

## How to Use This Project

1. Run `generate_headcount_data.py` to produce the four CSV files in `/data/`
2. Execute `headcount_analysis.sql` in any SQL environment (PostgreSQL, MySQL, SQLite, or BigQuery) after loading the CSVs into the relevant tables
3. Import the CSVs into Power BI Desktop and apply the DAX measures from `headcount_forecasting_dax.md` to build the interactive report

---

## Project Structure

```
project-04-headcount-forecasting/
│
├── generate_headcount_data.py     # Python simulation engine
├── headcount_analysis.sql         # SQL analytical queries (9 queries)
├── headcount_forecasting_dax.md   # Power BI DAX measures (23 measures)
├── README.md                      # This file
│
└── data/                          # Generated by running the Python script
    ├── employees.csv
    ├── headcount_monthly.csv
    ├── separations.csv
    └── new_hires.csv
```

---

## About the Author

Oluwatobi Abanishe is an HR Analyst and BI Specialist with experience in SAP HCM, Power BI, SQL, and Python, focused on translating workforce data into actionable planning decisions.

[LinkedIn](https://linkedin.com/in/oluwatobiabanishe) | [GitHub](https://github.com/TobiAbanishe) | tobi.abanishe@gmail.com
