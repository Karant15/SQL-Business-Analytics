# SQL Business Analytics Dashboard

25 advanced SQL queries across two real-world datasets, healthcare and supply chain - demonstrating SQL proficiency from basic aggregations through advanced window functions, CTEs, and subqueries.

---

## Live Dashboard

[Click here to open the live dashboard](#) - (http://localhost:8501/)

---

## The Problem This Solves

SQL is required in 85% of analyst job postings. Most candidates list it on their resume. Few can demonstrate it across multiple SQL levels, multiple datasets, and real business questions simultaneously.

This project does exactly that — 25 queries ranging from basic GROUP BY through advanced window functions like LAG, LEAD, RANK, running totals, and moving averages — all running against real data, all answering genuine business questions, all visible and reproducible on GitHub.

---

## Two Real Datasets — One Database

Both datasets were loaded into a single SQLite database for cross-domain analysis.

| Dataset | Source | Records | Columns |
|---------|--------|---------|---------|
| CMS Medicare Provider Data 2022 | data.cms.gov - US Government | 50,000 providers | 28 |
| DataCo Supply Chain Dataset | Mendeley Data | 50,000 orders | 53 |

---

## 25 SQL Queries - By Level

### Basic SQL - 6 Queries
Foundations every analyst must know.

| Query | Business Question | Concepts |
|-------|------------------|----------|
| HC_01 | Which specialties have the most providers? | GROUP BY COUNT ORDER BY |
| HC_02 | Which states generate the most Medicare revenue? | SUM GROUP BY multi-column |
| HC_03 | Which specialties command the highest payments? | AVG HAVING GROUP BY |
| SC_01 | Which regions have the worst delivery performance? | SUM ROUND percentage |
| SC_02 | Which product categories drive most revenue? | SUM AVG multi-aggregation |
| SC_06 | Which global markets are most profitable? | Multi-metric market comparison |

### Intermediate SQL - 9 Queries
Business logic, conditional grouping, and date functions.

| Query | Business Question | Concepts |
|-------|------------------|----------|
| HC_04 | Which states have provider shortages? | CASE WHEN ratio NULLIF |
| HC_08 | Drug vs non-drug service comparison | CASE WHEN categorical grouping |
| SC_03 | How do customer segments differ in value? | Multiple aggregations ratio |
| SC_04 | Which shipping modes are failing? | CASE WHEN performance rating |
| SC_05 | How has revenue trended monthly? | DATE functions SUBSTR |
| SC_11 | Which departments have the best margins? | Profitability ranking |
| XD_01 | Healthcare executive KPI summary | Single query all metrics |
| XD_02 | Supply chain executive KPI summary | Single query all metrics |
| XD_04 | Which specialties pay above the national average? | Subquery in HAVING clause |

### Advanced SQL - 9 Queries
Window functions, CTEs, cross-domain analysis.

| Query | Business Question | Concepts |
|-------|------------------|----------|
| HC_05 | Rank specialties by payment within each state | RANK() OVER PARTITION BY |
| HC_06 | Which providers are in top 10%? | NTILE() window function |
| HC_07 | Cumulative Medicare revenue by state | SUM() OVER running total |
| SC_07 | Rank regions by revenue | RANK DENSE_RANK ROW_NUMBER |
| SC_08 | How does the late delivery rate change monthly? | LAG() trend analysis |
| SC_09 | Cumulative revenue + moving average | Running window 3-month avg |
| SC_10 | ABC inventory classification | CTE WITH cumulative percentage |
| XD_03 | Top states - healthcare vs supply chain | Two CTEs + LEFT JOIN |
| XD_05 | Next month revenue for forward planning | LEAD() forecasting |

---

## Key SQL Concepts Demonstrated

```sql
-- Window Functions
RANK() OVER (PARTITION BY state ORDER BY revenue DESC)
DENSE_RANK() OVER (ORDER BY revenue DESC)
ROW_NUMBER() OVER (ORDER BY revenue DESC)
NTILE(10) OVER (ORDER BY payment DESC)

-- Trend Analysis
LAG(revenue) OVER (ORDER BY month)
LEAD(revenue) OVER (ORDER BY month)

-- Running Totals and Moving Averages
SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- CTEs
WITH product_revenue AS (...),
cumulative AS (SELECT ..., SUM() OVER (...) FROM product_revenue)
SELECT ..., CASE WHEN cum_pct <= 80 THEN 'A' ... END FROM cumulative

-- Subqueries
HAVING AVG(payment) > (SELECT AVG(payment) FROM healthcare_providers)

-- Cross Domain JOIN
FROM hc_states h LEFT JOIN sc_states s ON h.State = s.State
```

---

## Dashboard - 5 Tabs

| Tab | What It Shows |
|-----|--------------|
| Healthcare SQL | Provider counts, revenue by state, shortage analysis, above-average specialties |
| Supply Chain SQL | Late delivery by region, revenue by category, monthly trends, customer segments |
| Advanced Window Functions | RANK/LAG/LEAD demo, moving average chart, ABC inventory CTE |
| Cross Domain Analysis | Executive KPI summaries, top states comparison across both datasets |
| Live SQL Explorer | Write and run any SQL query against the real database in real time |

---

## Project Structure

```
sql-business-analytics/
│
├── data/
│   ├── cms_healthcare.csv        - CMS Medicare sample data
│   └── supply_chain.csv          - DataCo supply chain sample
│
├── outputs/
│   └── sql/
│       ├── 00_QUERY_SUMMARY.csv  - All 25 queries indexed
│       ├── HC_01_*.csv           - Healthcare query results
│       ├── SC_01_*.csv           - Supply chain query results
│       └── XD_01_*.csv           - Cross domain query results
│
├── setup_database.py   - Loads CSV data into SQLite
├── sql_queries.py      - Runs all 25 queries and saves outputs
├── dashboard.py        - Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## How To Run Locally

```bash
git clone https://github.com/Karant15/SQL-Business-Analytics.git
cd SQL-Business-Analytics
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Setup database
python setup_database.py

# Run all 25 queries
python sql_queries.py

# Launch dashboard
streamlit run dashboard.py
```

---

## Interview Value

Every SQL query in this project maps to a real interview question:

- **Basic:** Required at entry level - GROUP BY, aggregations, filtering
- **Intermediate:** Tested at 80% of technical interviews at J&J, Merck, Cognizant
- **Advanced:** Differentiates from 90% of candidates - window functions, CTEs
- **Live Explorer:** Demonstrates ability to write ad hoc SQL on demand

---

## Data Sources

- CMS Medicare: https://data.cms.gov/provider-summary-by-type-of-service
- DataCo Supply Chain: https://data.mendeley.com/datasets/8gx2fvg2k6/5

---

## About

**Karan Trivedi** | MS Data Analytics, Webster University (Dec 2024)
- Lean Six Sigma Black Belt - Benchmark Six Sigma (2021)
- 7+ years of healthcare, recruitment, and business analytics
- Former Senior Accounts Manager - 30+ NHS hospital accounts

krntrivedi@gmail.com
[LinkedIn](https://www.linkedin.com/in/karan-r-trivedi-b9a96a56)
[GitHub](https://github.com/Karant15)
