-- ─────────────────────────────────────────────────────────────────────────────
-- headcount_analysis.sql
-- Project 4: Headcount Forecasting | NorthBridge Financial
-- Author: Oluwutobi Abanishe | github.com/TobiAbanishe
-- ─────────────────────────────────────────────────────────────────────────────
-- Tables used:
--   headcount_monthly  (year, month, month_date, department, closing_headcount,
--                       new_hires, separations)
--   employees          (employee_id, department, job_level, location, hire_date,
--                       status, separation_date, separation_type)
--   separations        (employee_id, department, job_level, location,
--                       separation_date, separation_type, year, month)
--   new_hires          (employee_id, department, job_level, location,
--                       hire_date, year, month)
-- ─────────────────────────────────────────────────────────────────────────────


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 1: Monthly Headcount Waterfall by Department
-- Opening headcount + new hires - separations = closing headcount (integrity check)
-- ═════════════════════════════════════════════════════════════════════════════

SELECT
    h.year,
    h.month,
    h.month_date,
    h.department,
    LAG(h.closing_headcount) OVER (
        PARTITION BY h.department
        ORDER BY h.year, h.month
    )                                                       AS opening_headcount,
    h.new_hires,
    h.separations,
    h.closing_headcount,
    h.closing_headcount - LAG(h.closing_headcount) OVER (
        PARTITION BY h.department
        ORDER BY h.year, h.month
    )                                                       AS net_headcount_change
FROM headcount_monthly h
ORDER BY h.department, h.year, h.month;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 2: Annualized Attrition Rate by Department and Year
-- Formula: (Total Separations / Average Headcount) * 100
-- Benchmark: SHRM 2023 reports 17.1% avg voluntary attrition in financial services
-- ═════════════════════════════════════════════════════════════════════════════

WITH annual_summary AS (
    SELECT
        year,
        department,
        SUM(separations)                                        AS total_separations,
        AVG(closing_headcount)                                  AS avg_headcount,
        SUM(new_hires)                                          AS total_hires
    FROM headcount_monthly
    GROUP BY year, department
)
SELECT
    year,
    department,
    total_separations,
    ROUND(avg_headcount, 1)                                     AS avg_headcount,
    total_hires,
    ROUND((total_separations * 1.0 / NULLIF(avg_headcount, 0)) * 100, 2)
                                                                AS attrition_rate_pct,
    ROUND((total_hires * 1.0 / NULLIF(avg_headcount, 0)) * 100, 2)
                                                                AS hiring_rate_pct
FROM annual_summary
ORDER BY year, attrition_rate_pct DESC;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 3: Year-over-Year Headcount Change by Department
-- Compares December closing headcount across years
-- ═════════════════════════════════════════════════════════════════════════════

WITH dec_snapshot AS (
    SELECT
        year,
        department,
        closing_headcount
    FROM headcount_monthly
    WHERE month = 12
)
SELECT
    curr.department,
    curr.year                                                   AS current_year,
    curr.closing_headcount                                      AS current_headcount,
    prev.closing_headcount                                      AS prior_year_headcount,
    curr.closing_headcount - prev.closing_headcount             AS yoy_change,
    ROUND(
        (curr.closing_headcount - prev.closing_headcount) * 100.0
        / NULLIF(prev.closing_headcount, 0),
        2
    )                                                           AS yoy_change_pct
FROM dec_snapshot curr
LEFT JOIN dec_snapshot prev
    ON curr.department = prev.department
    AND curr.year      = prev.year + 1
WHERE curr.year > (SELECT MIN(year) FROM dec_snapshot)
ORDER BY curr.year, yoy_change_pct DESC;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 4: Separation Breakdown by Type and Department
-- Splits voluntary vs. involuntary vs. retirement to support root-cause analysis
-- ═════════════════════════════════════════════════════════════════════════════

SELECT
    EXTRACT(YEAR FROM separation_date)                          AS year,
    department,
    separation_type,
    COUNT(*)                                                    AS separation_count,
    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (
            PARTITION BY EXTRACT(YEAR FROM separation_date), department
        ),
        1
    )                                                           AS pct_of_dept_seps
FROM separations
GROUP BY
    EXTRACT(YEAR FROM separation_date),
    department,
    separation_type
ORDER BY year, department, separation_count DESC;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 5: Separation Breakdown by Job Level
-- SHRM benchmark: Analyst-level attrition runs 2-3x higher than Director/VP
-- ═════════════════════════════════════════════════════════════════════════════

SELECT
    EXTRACT(YEAR FROM separation_date)                          AS year,
    job_level,
    separation_type,
    COUNT(*)                                                    AS separations,
    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (
            PARTITION BY EXTRACT(YEAR FROM separation_date)
        ),
        2
    )                                                           AS pct_of_total_seps
FROM separations
GROUP BY
    EXTRACT(YEAR FROM separation_date),
    job_level,
    separation_type
ORDER BY year, separations DESC;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 6: Rolling 3-Month Attrition Rate by Department
-- Smooths monthly noise; useful for trend detection in Power BI tooltips
-- ═════════════════════════════════════════════════════════════════════════════

WITH monthly_rates AS (
    SELECT
        year,
        month,
        month_date,
        department,
        closing_headcount,
        separations,
        ROUND(separations * 100.0 / NULLIF(closing_headcount, 0), 2) AS monthly_attrition_pct
    FROM headcount_monthly
)
SELECT
    year,
    month,
    month_date,
    department,
    monthly_attrition_pct,
    ROUND(
        AVG(monthly_attrition_pct) OVER (
            PARTITION BY department
            ORDER BY year, month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    )                                                           AS rolling_3m_attrition_pct
FROM monthly_rates
ORDER BY department, year, month;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 7: Simple Headcount Forecast — Next 3 Months
-- Method: trailing 6-month average net change applied forward
-- (Baseline model; intended to be enhanced in Power BI with DAX)
-- ═════════════════════════════════════════════════════════════════════════════

WITH net_changes AS (
    SELECT
        department,
        year,
        month,
        month_date,
        closing_headcount,
        closing_headcount - LAG(closing_headcount) OVER (
            PARTITION BY department ORDER BY year, month
        )                                                       AS net_change
    FROM headcount_monthly
),
trailing_avg AS (
    SELECT
        department,
        month_date,
        closing_headcount,
        ROUND(
            AVG(net_change) OVER (
                PARTITION BY department
                ORDER BY year, month
                ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
            ),
            1
        )                                                       AS avg_monthly_net_change
    FROM net_changes
),
latest AS (
    SELECT
        department,
        closing_headcount                                       AS last_known_headcount,
        avg_monthly_net_change
    FROM trailing_avg
    WHERE month_date = (SELECT MAX(month_date) FROM headcount_monthly)
)
SELECT
    department,
    last_known_headcount,
    avg_monthly_net_change,
    ROUND(last_known_headcount + avg_monthly_net_change,       0) AS forecast_month_1,
    ROUND(last_known_headcount + (avg_monthly_net_change * 2), 0) AS forecast_month_2,
    ROUND(last_known_headcount + (avg_monthly_net_change * 3), 0) AS forecast_month_3
FROM latest
ORDER BY department;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 8: New Hire Profile Analysis
-- Understand hiring patterns by level, department, and location
-- ═════════════════════════════════════════════════════════════════════════════

SELECT
    EXTRACT(YEAR FROM hire_date)                                AS year,
    department,
    job_level,
    location,
    COUNT(*)                                                    AS new_hires,
    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (
            PARTITION BY EXTRACT(YEAR FROM hire_date), department
        ),
        1
    )                                                           AS pct_of_dept_hires
FROM new_hires
GROUP BY
    EXTRACT(YEAR FROM hire_date),
    department,
    job_level,
    location
ORDER BY year, department, new_hires DESC;


-- ═════════════════════════════════════════════════════════════════════════════
-- QUERY 9: Organisation-Wide Headcount KPI Summary by Year
-- Single-row executive summary per year
-- ═════════════════════════════════════════════════════════════════════════════

WITH dec_hc AS (
    SELECT year, SUM(closing_headcount) AS dec_headcount
    FROM headcount_monthly
    WHERE month = 12
    GROUP BY year
),
annual AS (
    SELECT
        year,
        SUM(new_hires)    AS total_hires,
        SUM(separations)  AS total_seps,
        AVG(closing_headcount) AS avg_headcount
    FROM headcount_monthly
    GROUP BY year
)
SELECT
    a.year,
    d.dec_headcount,
    a.avg_headcount,
    a.total_hires,
    a.total_seps,
    a.total_hires - a.total_seps                                AS net_headcount_change,
    ROUND(a.total_seps * 100.0 / NULLIF(a.avg_headcount, 0), 2)
                                                                AS attrition_rate_pct,
    ROUND(
        (d.dec_headcount - LAG(d.dec_headcount) OVER (ORDER BY a.year))
        * 100.0
        / NULLIF(LAG(d.dec_headcount) OVER (ORDER BY a.year), 0),
        2
    )                                                           AS yoy_headcount_growth_pct
FROM annual a
JOIN dec_hc d ON a.year = d.year
ORDER BY a.year;
