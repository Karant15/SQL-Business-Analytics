import pandas as pd
import sqlite3
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('outputs/sql', exist_ok=True)
conn = sqlite3.connect('business_analytics.db')

print("="*60)
print("SQL BUSINESS ANALYTICS - 25 QUERIES")
print("Healthcare + Supply Chain | Real Data | All SQL Levels")
print("="*60)

queries = {

    # ── HEALTHCARE QUERIES ─────────────────────────────────────

    "HC_01_Top_Specialties_By_Provider_Count": {
        "business_question": "Which medical specialties have the most providers nationally?",
        "sql_level": "Basic - GROUP BY COUNT ORDER BY",
        "query": """
            SELECT
                Rndrng_Prvdr_Type as Specialty,
                COUNT(DISTINCT Rndrng_NPI) as Provider_Count,
                COUNT(*) as Total_Services,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Medicare_Payment
            FROM healthcare_providers
            GROUP BY Rndrng_Prvdr_Type
            ORDER BY Provider_Count DESC
            LIMIT 20
        """
    },

    "HC_02_Revenue_By_State": {
        "business_question": "Which states generate the most Medicare revenue?",
        "sql_level": "Basic - SUM GROUP BY ORDER BY",
        "query": """
            SELECT
                Rndrng_Prvdr_State_Abrvtn as State,
                COUNT(DISTINCT Rndrng_NPI) as Providers,
                ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 2) as Total_Medicare_Revenue,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment_Per_Service,
                SUM(Tot_Benes) as Total_Patients
            FROM healthcare_providers
            GROUP BY Rndrng_Prvdr_State_Abrvtn
            ORDER BY Total_Medicare_Revenue DESC
            LIMIT 20
        """
    },

    "HC_03_High_Value_Specialties": {
        "business_question": "Which specialties command the highest average Medicare payments?",
        "sql_level": "Basic - AVG HAVING GROUP BY",
        "query": """
            SELECT
                Rndrng_Prvdr_Type as Specialty,
                COUNT(DISTINCT Rndrng_NPI) as Provider_Count,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment,
                ROUND(MAX(Avg_Mdcr_Pymt_Amt), 2) as Max_Payment,
                ROUND(MIN(Avg_Mdcr_Pymt_Amt), 2) as Min_Payment,
                SUM(Tot_Benes) as Total_Patients
            FROM healthcare_providers
            GROUP BY Rndrng_Prvdr_Type
            HAVING Provider_Count >= 10
            ORDER BY Avg_Payment DESC
            LIMIT 20
        """
    },

    "HC_04_Provider_Shortage_States": {
        "business_question": "Which states have the fewest providers relative to patient volume?",
        "sql_level": "Intermediate - Calculated ratio CASE WHEN",
        "query": """
            SELECT
                Rndrng_Prvdr_State_Abrvtn as State,
                COUNT(DISTINCT Rndrng_NPI) as Providers,
                SUM(Tot_Benes) as Total_Patients,
                ROUND(CAST(SUM(Tot_Benes) AS FLOAT) /
                      NULLIF(COUNT(DISTINCT Rndrng_NPI), 0), 1)
                    as Patients_Per_Provider,
                CASE
                    WHEN CAST(SUM(Tot_Benes) AS FLOAT) /
                         NULLIF(COUNT(DISTINCT Rndrng_NPI), 0) > 500
                    THEN 'Critical Shortage'
                    WHEN CAST(SUM(Tot_Benes) AS FLOAT) /
                         NULLIF(COUNT(DISTINCT Rndrng_NPI), 0) > 300
                    THEN 'Moderate Shortage'
                    ELSE 'Adequate Supply'
                END as Shortage_Category
            FROM healthcare_providers
            GROUP BY Rndrng_Prvdr_State_Abrvtn
            ORDER BY Patients_Per_Provider DESC
            LIMIT 20
        """
    },

    "HC_05_Specialty_Payment_Ranking": {
        "business_question": "Rank specialties by payment within each state using window functions",
        "sql_level": "Advanced - RANK() OVER PARTITION BY",
        "query": """
            WITH state_specialty AS (
                SELECT
                    Rndrng_Prvdr_State_Abrvtn as State,
                    Rndrng_Prvdr_Type as Specialty,
                    ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment,
                    COUNT(DISTINCT Rndrng_NPI) as Providers
                FROM healthcare_providers
                GROUP BY State, Specialty
            )
            SELECT
                State,
                Specialty,
                Avg_Payment,
                Providers,
                RANK() OVER (
                    PARTITION BY State
                    ORDER BY Avg_Payment DESC
                ) as Payment_Rank_In_State
            FROM state_specialty
            WHERE Providers >= 5
            ORDER BY State, Payment_Rank_In_State
            LIMIT 50
        """
    },

    "HC_06_Provider_Performance_Percentile": {
        "business_question": "Which providers are in the top 10% for Medicare payments?",
        "sql_level": "Advanced - NTILE window function percentile",
        "query": """
            WITH provider_summary AS (
                SELECT
                    Rndrng_NPI as Provider_ID,
                    Rndrng_Prvdr_Last_Org_Name as Provider_Name,
                    Rndrng_Prvdr_Type as Specialty,
                    Rndrng_Prvdr_State_Abrvtn as State,
                    ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment,
                    SUM(Tot_Benes) as Total_Patients
                FROM healthcare_providers
                GROUP BY Provider_ID
            )
            SELECT
                Provider_ID,
                Provider_Name,
                Specialty,
                State,
                Avg_Payment,
                Total_Patients,
                NTILE(10) OVER (ORDER BY Avg_Payment DESC) as Decile,
                CASE WHEN NTILE(10) OVER (
                    ORDER BY Avg_Payment DESC) = 1
                THEN 'Top 10 Percent'
                ELSE 'Standard'
                END as Performance_Tier
            FROM provider_summary
            ORDER BY Avg_Payment DESC
            LIMIT 30
        """
    },

    "HC_07_Running_Total_By_State": {
        "business_question": "Show cumulative Medicare revenue as we add states ranked by revenue",
        "sql_level": "Advanced - SUM() OVER running total",
        "query": """
            WITH state_revenue AS (
                SELECT
                    Rndrng_Prvdr_State_Abrvtn as State,
                    ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 2) as Revenue
                FROM healthcare_providers
                GROUP BY State
                ORDER BY Revenue DESC
            )
            SELECT
                State,
                Revenue,
                ROUND(SUM(Revenue) OVER (
                    ORDER BY Revenue DESC
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ), 2) as Cumulative_Revenue,
                ROUND(Revenue * 100.0 / SUM(Revenue) OVER (), 2)
                    as Pct_Of_Total
            FROM state_revenue
            LIMIT 20
        """
    },

    "HC_08_Drug_Vs_NonDrug_Comparison": {
        "business_question": "How do drug services compare to non-drug services in cost and volume?",
        "sql_level": "Intermediate - CASE WHEN grouping comparison",
        "query": """
            SELECT
                CASE WHEN HCPCS_Drug_Ind = 'Y'
                     THEN 'Drug Service'
                     ELSE 'Non-Drug Service'
                END as Service_Type,
                COUNT(*) as Total_Records,
                COUNT(DISTINCT Rndrng_NPI) as Unique_Providers,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment,
                ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 2) as Total_Revenue,
                SUM(Tot_Benes) as Total_Patients
            FROM healthcare_providers
            GROUP BY Service_Type
            ORDER BY Total_Revenue DESC
        """
    },

    # ── SUPPLY CHAIN QUERIES ───────────────────────────────────

    "SC_01_Late_Delivery_By_Region": {
        "business_question": "Which regions have the worst on-time delivery performance?",
        "sql_level": "Basic - GROUP BY SUM ROUND",
        "query": """
            SELECT
                [Order Region] as Region,
                COUNT(*) as Total_Orders,
                SUM(Late_delivery_risk) as Late_Orders,
                ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)
                    as Late_Rate_Pct,
                ROUND(AVG([Days for shipping (real)]), 1)
                    as Avg_Actual_Days,
                ROUND(AVG([Days for shipment (scheduled)]), 1)
                    as Avg_Scheduled_Days
            FROM supply_chain_orders
            GROUP BY Region
            ORDER BY Late_Rate_Pct DESC
        """
    },

    "SC_02_Revenue_By_Category": {
        "business_question": "Which product categories drive the most revenue and profit?",
        "sql_level": "Basic - SUM AVG GROUP BY multi-column",
        "query": """
            SELECT
                [Category Name] as Category,
                COUNT(*) as Total_Orders,
                ROUND(SUM(Sales), 2) as Total_Revenue,
                ROUND(SUM([Order Profit Per Order]), 2) as Total_Profit,
                ROUND(AVG([Order Item Profit Ratio]) * 100, 1)
                    as Avg_Margin_Pct,
                ROUND(AVG(Sales), 2) as Avg_Order_Value
            FROM supply_chain_orders
            GROUP BY Category
            ORDER BY Total_Revenue DESC
            LIMIT 15
        """
    },

    "SC_03_Customer_Segment_Analysis": {
        "business_question": "How do customer segments differ in value and behaviour?",
        "sql_level": "Intermediate - multiple aggregations ratio calculation",
        "query": """
            SELECT
                [Customer Segment] as Segment,
                COUNT(DISTINCT [Customer Id]) as Unique_Customers,
                COUNT(*) as Total_Orders,
                ROUND(SUM(Sales), 2) as Total_Revenue,
                ROUND(AVG(Sales), 2) as Avg_Order_Value,
                ROUND(SUM([Order Profit Per Order]), 2) as Total_Profit,
                ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)
                    as Late_Rate_Pct,
                ROUND(CAST(COUNT(*) AS FLOAT) /
                      NULLIF(COUNT(DISTINCT [Customer Id]), 0), 1)
                    as Orders_Per_Customer
            FROM supply_chain_orders
            GROUP BY Segment
            ORDER BY Total_Revenue DESC
        """
    },

    "SC_04_Shipping_Mode_Performance": {
        "business_question": "Which shipping modes are failing their customers most?",
        "sql_level": "Intermediate - CASE WHEN performance rating",
        "query": """
            SELECT
                [Shipping Mode] as Mode,
                COUNT(*) as Total_Orders,
                SUM(Late_delivery_risk) as Late_Orders,
                ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)
                    as Late_Rate_Pct,
                ROUND(AVG([Days for shipping (real)]), 1)
                    as Avg_Actual_Days,
                ROUND(AVG([Days for shipment (scheduled)]), 1)
                    as Avg_Scheduled_Days,
                ROUND(AVG([Days for shipping (real)]) -
                      AVG([Days for shipment (scheduled)]), 1)
                    as Avg_Delay_Days,
                CASE
                    WHEN SUM(Late_delivery_risk) * 100.0 /
                         COUNT(*) > 60 THEN 'Critical'
                    WHEN SUM(Late_delivery_risk) * 100.0 /
                         COUNT(*) > 40 THEN 'Poor'
                    ELSE 'Acceptable'
                END as Performance_Rating
            FROM supply_chain_orders
            GROUP BY Mode
            ORDER BY Late_Rate_Pct DESC
        """
    },

    "SC_05_Monthly_Revenue_Trend": {
        "business_question": "How has revenue trended month over month?",
        "sql_level": "Intermediate - date functions substring grouping",
        "query": """
            SELECT
                SUBSTR([order date (DateOrders)], 1, 7) as Year_Month,
                COUNT(*) as Total_Orders,
                ROUND(SUM(Sales), 2) as Total_Revenue,
                ROUND(AVG(Sales), 2) as Avg_Order_Value,
                SUM(Late_delivery_risk) as Late_Orders,
                ROUND(SUM(Late_delivery_risk) * 100.0 /
                      COUNT(*), 1) as Late_Rate_Pct
            FROM supply_chain_orders
            WHERE [order date (DateOrders)] IS NOT NULL
            GROUP BY Year_Month
            ORDER BY Year_Month
        """
    },

    "SC_06_Market_Performance": {
        "business_question": "Which global markets are most profitable?",
        "sql_level": "Basic - multi-metric market comparison",
        "query": """
            SELECT
                Market,
                COUNT(*) as Total_Orders,
                COUNT(DISTINCT [Customer Id]) as Unique_Customers,
                ROUND(SUM(Sales), 2) as Total_Revenue,
                ROUND(SUM([Order Profit Per Order]), 2) as Total_Profit,
                ROUND(AVG([Order Item Profit Ratio]) * 100, 1)
                    as Avg_Margin_Pct,
                ROUND(SUM(Late_delivery_risk) * 100.0 /
                      COUNT(*), 1) as Late_Rate_Pct
            FROM supply_chain_orders
            GROUP BY Market
            ORDER BY Total_Revenue DESC
        """
    },

    "SC_07_Revenue_Rank_By_Region": {
        "business_question": "Rank regions by revenue using SQL window functions",
        "sql_level": "Advanced - RANK() DENSE_RANK() ROW_NUMBER()",
        "query": """
            WITH region_summary AS (
                SELECT
                    [Order Region] as Region,
                    Market,
                    ROUND(SUM(Sales), 2) as Total_Revenue,
                    ROUND(SUM([Order Profit Per Order]), 2) as Total_Profit,
                    COUNT(*) as Total_Orders
                FROM supply_chain_orders
                GROUP BY Region, Market
            )
            SELECT
                Region,
                Market,
                Total_Revenue,
                Total_Profit,
                Total_Orders,
                RANK() OVER (ORDER BY Total_Revenue DESC)
                    as Revenue_Rank,
                DENSE_RANK() OVER (ORDER BY Total_Revenue DESC)
                    as Dense_Rank,
                ROW_NUMBER() OVER (ORDER BY Total_Revenue DESC)
                    as Row_Number
            FROM region_summary
            ORDER BY Revenue_Rank
        """
    },

    "SC_08_Late_Orders_Lag_Analysis": {
        "business_question": "How does late delivery rate change month over month?",
        "sql_level": "Advanced - LAG() window function trend analysis",
        "query": """
            WITH monthly_late AS (
                SELECT
                    SUBSTR([order date (DateOrders)], 1, 7) as Month,
                    ROUND(SUM(Late_delivery_risk) * 100.0 /
                          COUNT(*), 1) as Late_Rate,
                    COUNT(*) as Orders
                FROM supply_chain_orders
                WHERE [order date (DateOrders)] IS NOT NULL
                GROUP BY Month
            )
            SELECT
                Month,
                Late_Rate,
                Orders,
                LAG(Late_Rate) OVER (ORDER BY Month)
                    as Prev_Month_Late_Rate,
                ROUND(Late_Rate - LAG(Late_Rate) OVER (
                    ORDER BY Month), 1) as Month_Over_Month_Change,
                CASE
                    WHEN Late_Rate > LAG(Late_Rate) OVER (
                        ORDER BY Month) THEN 'Worsening'
                    WHEN Late_Rate < LAG(Late_Rate) OVER (
                        ORDER BY Month) THEN 'Improving'
                    ELSE 'Stable'
                END as Trend
            FROM monthly_late
            ORDER BY Month
        """
    },

    "SC_09_Running_Revenue_Total": {
        "business_question": "Show cumulative revenue building up over time",
        "sql_level": "Advanced - SUM() OVER cumulative window",
        "query": """
            WITH monthly AS (
                SELECT
                    SUBSTR([order date (DateOrders)], 1, 7) as Month,
                    ROUND(SUM(Sales), 2) as Monthly_Revenue
                FROM supply_chain_orders
                WHERE [order date (DateOrders)] IS NOT NULL
                GROUP BY Month
            )
            SELECT
                Month,
                Monthly_Revenue,
                ROUND(SUM(Monthly_Revenue) OVER (
                    ORDER BY Month
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND CURRENT ROW
                ), 2) as Cumulative_Revenue,
                ROUND(AVG(Monthly_Revenue) OVER (
                    ORDER BY Month
                    ROWS BETWEEN 2 PRECEDING
                    AND CURRENT ROW
                ), 2) as Three_Month_Moving_Avg
            FROM monthly
            ORDER BY Month
        """
    },

    "SC_10_ABC_Inventory_CTE": {
        "business_question": "Classify products into ABC inventory categories using CTEs",
        "sql_level": "Advanced - CTE WITH clause cumulative percentage",
        "query": """
            WITH product_revenue AS (
                SELECT
                    [Product Name] as Product,
                    ROUND(SUM(Sales), 2) as Total_Revenue,
                    COUNT(*) as Times_Ordered
                FROM supply_chain_orders
                GROUP BY Product
                ORDER BY Total_Revenue DESC
            ),
            cumulative AS (
                SELECT
                    Product,
                    Total_Revenue,
                    Times_Ordered,
                    ROUND(SUM(Total_Revenue) OVER (
                        ORDER BY Total_Revenue DESC
                        ROWS BETWEEN UNBOUNDED PRECEDING
                        AND CURRENT ROW
                    ) * 100.0 / SUM(Total_Revenue) OVER (), 1)
                        as Cumulative_Pct
                FROM product_revenue
            )
            SELECT
                Product,
                Total_Revenue,
                Times_Ordered,
                Cumulative_Pct,
                CASE
                    WHEN Cumulative_Pct <= 80 THEN 'A - Top 80pct'
                    WHEN Cumulative_Pct <= 95 THEN 'B - Middle 15pct'
                    ELSE 'C - Bottom 5pct'
                END as ABC_Class
            FROM cumulative
            ORDER BY Total_Revenue DESC
            LIMIT 30
        """
    },

    "SC_11_Department_Profitability": {
        "business_question": "Which departments deliver the best profit margins?",
        "sql_level": "Intermediate - profitability ranking subquery",
        "query": """
            SELECT
                [Department Name] as Department,
                COUNT(*) as Total_Orders,
                ROUND(SUM(Sales), 2) as Total_Revenue,
                ROUND(SUM([Order Profit Per Order]), 2) as Total_Profit,
                ROUND(AVG([Order Item Profit Ratio]) * 100, 2)
                    as Avg_Margin_Pct,
                SUM(Late_delivery_risk) as Late_Orders,
                ROUND(SUM(Late_delivery_risk) * 100.0 /
                      COUNT(*), 1) as Late_Rate_Pct
            FROM supply_chain_orders
            GROUP BY Department
            ORDER BY Avg_Margin_Pct DESC
        """
    },

    # ── CROSS DOMAIN QUERIES ───────────────────────────────────

    "XD_01_Healthcare_State_Summary": {
        "business_question": "Executive KPI summary for healthcare - single query all metrics",
        "sql_level": "Intermediate - executive summary query",
        "query": """
            SELECT
                COUNT(DISTINCT Rndrng_NPI) as Total_Providers,
                COUNT(DISTINCT Rndrng_Prvdr_Type) as Specialties,
                COUNT(DISTINCT Rndrng_Prvdr_State_Abrvtn) as States,
                SUM(Tot_Benes) as Total_Patients,
                ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 2)
                    as Total_Medicare_Revenue,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment,
                MAX(Avg_Mdcr_Pymt_Amt) as Max_Single_Payment,
                COUNT(DISTINCT HCPCS_Cd) as Unique_Service_Codes
            FROM healthcare_providers
        """
    },

    "XD_02_Supply_Chain_KPI_Summary": {
        "business_question": "Executive KPI summary for supply chain - single query all metrics",
        "sql_level": "Intermediate - executive summary query",
        "query": """
            SELECT
                COUNT(*) as Total_Orders,
                COUNT(DISTINCT [Customer Id]) as Unique_Customers,
                COUNT(DISTINCT [Product Name]) as Unique_Products,
                COUNT(DISTINCT [Order Region]) as Regions,
                ROUND(SUM(Sales), 2) as Total_Revenue,
                ROUND(SUM([Order Profit Per Order]), 2) as Total_Profit,
                ROUND(AVG([Order Item Profit Ratio]) * 100, 1)
                    as Avg_Margin_Pct,
                SUM(Late_delivery_risk) as Late_Orders,
                ROUND(SUM(Late_delivery_risk) * 100.0 /
                      COUNT(*), 1) as Overall_Late_Rate_Pct,
                ROUND(AVG(Sales), 2) as Avg_Order_Value
            FROM supply_chain_orders
        """
    },

    "XD_03_Top_States_Healthcare_Vs_Supply": {
        "business_question": "Compare top states in healthcare revenue vs supply chain orders",
        "sql_level": "Advanced - two CTEs combined for cross domain comparison",
        "query": """
            WITH hc_states AS (
                SELECT
                    Rndrng_Prvdr_State_Abrvtn as State,
                    ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 2)
                        as HC_Revenue,
                    COUNT(DISTINCT Rndrng_NPI) as HC_Providers,
                    RANK() OVER (
                        ORDER BY SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs) DESC
                    ) as HC_Rank
                FROM healthcare_providers
                GROUP BY State
            ),
            sc_states AS (
                SELECT
                    [Customer State] as State,
                    ROUND(SUM(Sales), 2) as SC_Revenue,
                    COUNT(*) as SC_Orders,
                    RANK() OVER (
                        ORDER BY SUM(Sales) DESC
                    ) as SC_Rank
                FROM supply_chain_orders
                WHERE [Customer State] IS NOT NULL
                GROUP BY State
            )
            SELECT
                h.State,
                h.HC_Revenue,
                h.HC_Providers,
                h.HC_Rank as Healthcare_Revenue_Rank,
                s.SC_Revenue,
                s.SC_Orders,
                s.SC_Rank as SupplyChain_Revenue_Rank
            FROM hc_states h
            LEFT JOIN sc_states s ON h.State = s.State
            WHERE h.HC_Rank <= 15
            ORDER BY h.HC_Rank
        """
    },

    "XD_04_Subquery_Above_Average": {
        "business_question": "Which healthcare specialties pay above the national average?",
        "sql_level": "Intermediate - subquery in WHERE clause",
        "query": """
            SELECT
                Rndrng_Prvdr_Type as Specialty,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) as Avg_Payment,
                COUNT(DISTINCT Rndrng_NPI) as Providers,
                ROUND(AVG(Avg_Mdcr_Pymt_Amt) - (
                    SELECT AVG(Avg_Mdcr_Pymt_Amt)
                    FROM healthcare_providers
                ), 2) as Above_National_Average_By
            FROM healthcare_providers
            GROUP BY Specialty
            HAVING AVG(Avg_Mdcr_Pymt_Amt) > (
                SELECT AVG(Avg_Mdcr_Pymt_Amt)
                FROM healthcare_providers
            )
            ORDER BY Avg_Payment DESC
            LIMIT 15
        """
    },

    "XD_05_Lead_Revenue_Growth": {
        "business_question": "Show next month revenue alongside current for forward planning",
        "sql_level": "Advanced - LEAD() window function forecasting",
        "query": """
            WITH monthly AS (
                SELECT
                    SUBSTR([order date (DateOrders)], 1, 7) as Month,
                    ROUND(SUM(Sales), 2) as Revenue,
                    COUNT(*) as Orders
                FROM supply_chain_orders
                WHERE [order date (DateOrders)] IS NOT NULL
                GROUP BY Month
            )
            SELECT
                Month,
                Revenue,
                Orders,
                LEAD(Revenue) OVER (ORDER BY Month)
                    as Next_Month_Revenue,
                ROUND(
                    (LEAD(Revenue) OVER (ORDER BY Month) - Revenue)
                    * 100.0 / NULLIF(Revenue, 0)
                , 1) as Projected_Growth_Pct
            FROM monthly
            ORDER BY Month
        """
    }
}

# Run all queries and save results
print(f"\nRunning {len(queries)} SQL queries...\n")
summary = []

for name, details in queries.items():
    try:
        result = pd.read_sql_query(details['query'], conn)
        result.to_csv(f'outputs/sql/{name}.csv', index=False)
        summary.append({
            'Query': name,
            'Level': details['sql_level'].split(' - ')[0],
            'Business Question': details['business_question'],
            'Rows': len(result)
        })
        print(f"  {name}")
        print(f"  Level: {details['sql_level'].split(' - ')[0]}")
        print(f"  Question: {details['business_question']}")
        print(f"  Result: {len(result)} rows")
        print()
    except Exception as e:
        print(f"  ERROR in {name}: {e}\n")

# Save summary
summary_df = pd.DataFrame(summary)
summary_df.to_csv('outputs/sql/00_QUERY_SUMMARY.csv', index=False)

conn.close()

print("="*60)
print("ALL QUERIES COMPLETE")
print("="*60)
print(f"Total queries run: {len(summary)}")
print(f"\nSQL Levels covered:")
for level in ['Basic', 'Intermediate', 'Advanced']:
    count = len([s for s in summary if level in s['Level']])
    print(f"  {level}: {count} queries")
print(f"\nAll results saved in outputs/sql/")