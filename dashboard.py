import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="SQL Business Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── DATABASE ─────────────────────────────────────────────────────
@st.cache_resource
def get_database():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    for path in ['data/cms_healthcare.csv', 'data/cms_sample.csv']:
        if os.path.exists(path):
            hc = pd.read_csv(path, low_memory=False)
            hc.to_sql('healthcare_providers', conn, if_exists='replace', index=False)
            break
    for path in ['data/supply_chain.csv', 'data/supply_chain_sample.csv']:
        if os.path.exists(path):
            sc = pd.read_csv(path, encoding='latin-1', low_memory=False)
            sc.to_sql('supply_chain_orders', conn, if_exists='replace', index=False)
            break
    return conn

def run_query(query):
    conn = get_database()
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# ── HEADER ───────────────────────────────────────────────────────
st.title("🗄️ SQL Business Analytics Dashboard")
st.markdown("**25 Advanced SQL Queries | Healthcare + Supply Chain | Real Data | Window Functions · CTEs · Subqueries**")
st.markdown("*Demonstrating SQL proficiency from basic aggregations to advanced window functions across two real-world datasets*")
st.divider()

# ── KPI METRICS ──────────────────────────────────────────────────
hc_kpi = run_query("""
    SELECT
        COUNT(DISTINCT Rndrng_NPI)                          AS Providers,
        COUNT(DISTINCT Rndrng_Prvdr_Type)                   AS Specialties,
        SUM(Tot_Benes)                                      AS Patients,
        ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 0)       AS Revenue
    FROM healthcare_providers
""")

sc_kpi = run_query("""
    SELECT
        COUNT(*)                                                    AS Orders,
        ROUND(SUM(Sales), 0)                                        AS Revenue,
        ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)        AS Late_Rate,
        COUNT(DISTINCT [Product Name])                              AS Products
    FROM supply_chain_orders
""")

st.markdown("#### 🏥 Healthcare Dataset")
c1, c2, c3, c4 = st.columns(4)
if not hc_kpi.empty:
    c1.metric("Unique Providers",  f"{int(hc_kpi['Providers'][0]):,}")
    c2.metric("Specialties",       f"{int(hc_kpi['Specialties'][0]):,}")
    c3.metric("Total Patients",    f"{int(hc_kpi['Patients'][0]):,}")
    c4.metric("Medicare Revenue",  f"${float(hc_kpi['Revenue'][0]):,.0f}")
else:
    for col in [c1, c2, c3, c4]:
        col.metric("—", "N/A")

st.markdown("#### 📦 Supply Chain Dataset")
c5, c6, c7, c8 = st.columns(4)
if not sc_kpi.empty:
    c5.metric("Total Orders",       f"{int(sc_kpi['Orders'][0]):,}")
    c6.metric("Total Revenue",      f"${float(sc_kpi['Revenue'][0]):,.0f}")
    c7.metric("Late Delivery Rate", f"{float(sc_kpi['Late_Rate'][0])}%")
    c8.metric("Unique Products",    f"{int(sc_kpi['Products'][0]):,}")
else:
    for col in [c5, c6, c7, c8]:
        col.metric("—", "N/A")

st.divider()

# ── TABS ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏥 Healthcare SQL",
    "📦 Supply Chain SQL",
    "📊 Advanced Window Functions",
    "🔗 Cross Domain Analysis",
    "🔍 SQL Query Explorer"
])

# ── TAB 1: HEALTHCARE ────────────────────────────────────────────
with tab1:
    st.subheader("Healthcare Analytics SQL Queries")
    st.markdown("*CMS Medicare data — provider counts, revenue by state, shortage analysis*")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Q1: Top Specialties by Provider Count** *(Basic — GROUP BY COUNT)*")
        df1 = run_query("""
            SELECT Rndrng_Prvdr_Type                AS Specialty,
                   COUNT(DISTINCT Rndrng_NPI)       AS Provider_Count
            FROM healthcare_providers
            GROUP BY Specialty
            ORDER BY Provider_Count DESC
            LIMIT 15
        """)
        fig1 = px.bar(df1, x='Provider_Count', y='Specialty',
                      orientation='h', color='Provider_Count',
                      color_continuous_scale='Blues',
                      title='Provider Count by Specialty')
        fig1.update_layout(height=450, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("**Q2: Medicare Revenue by State** *(Basic — SUM GROUP BY)*")
        df2 = run_query("""
            SELECT Rndrng_Prvdr_State_Abrvtn                            AS State,
                   ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 0)        AS Total_Revenue
            FROM healthcare_providers
            GROUP BY State
            ORDER BY Total_Revenue DESC
            LIMIT 15
        """)
        fig2 = px.bar(df2, x='Total_Revenue', y='State',
                      orientation='h', color='Total_Revenue',
                      color_continuous_scale='Greens',
                      title='Medicare Revenue by State ($)')
        fig2.update_layout(height=450, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Q3: Provider Shortage Analysis** *(Intermediate — CASE WHEN ratio)*")
    df3 = run_query("""
        SELECT Rndrng_Prvdr_State_Abrvtn                                            AS State,
               COUNT(DISTINCT Rndrng_NPI)                                           AS Providers,
               SUM(Tot_Benes)                                                       AS Patients,
               ROUND(CAST(SUM(Tot_Benes) AS FLOAT) /
                     NULLIF(COUNT(DISTINCT Rndrng_NPI), 0), 1)                      AS Patients_Per_Provider,
               CASE
                   WHEN CAST(SUM(Tot_Benes) AS FLOAT) /
                        NULLIF(COUNT(DISTINCT Rndrng_NPI), 0) > 500 THEN 'Critical Shortage'
                   WHEN CAST(SUM(Tot_Benes) AS FLOAT) /
                        NULLIF(COUNT(DISTINCT Rndrng_NPI), 0) > 300 THEN 'Moderate Shortage'
                   ELSE 'Adequate'
               END                                                                  AS Category
        FROM healthcare_providers
        GROUP BY State
        ORDER BY Patients_Per_Provider DESC
        LIMIT 20
    """)
    fig3 = px.scatter(df3, x='Providers', y='Patients',
                      color='Category', hover_name='State',
                      size='Patients_Per_Provider',
                      color_discrete_map={
                          'Critical Shortage': '#A32D2D',
                          'Moderate Shortage': '#EF9F27',
                          'Adequate':          '#0F6E56'
                      },
                      title='Provider Supply vs Patient Demand by State')
    fig3.update_layout(height=420)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**Q4: Above Average Specialties** *(Intermediate — Subquery in HAVING)*")
    df4 = run_query("""
        SELECT Rndrng_Prvdr_Type                                                    AS Specialty,
               ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2)                                    AS Avg_Payment,
               COUNT(DISTINCT Rndrng_NPI)                                           AS Providers,
               ROUND(AVG(Avg_Mdcr_Pymt_Amt) -
                     (SELECT AVG(Avg_Mdcr_Pymt_Amt) FROM healthcare_providers), 2) AS Above_Average_By
        FROM healthcare_providers
        GROUP BY Specialty
        HAVING AVG(Avg_Mdcr_Pymt_Amt) > (SELECT AVG(Avg_Mdcr_Pymt_Amt) FROM healthcare_providers)
        ORDER BY Avg_Payment DESC
        LIMIT 15
    """)
    st.dataframe(df4, hide_index=True, use_container_width=True)

# ── TAB 2: SUPPLY CHAIN ──────────────────────────────────────────
with tab2:
    st.subheader("Supply Chain SQL Queries")
    st.markdown("*DataCo supply chain — delivery performance, revenue, customer segments*")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Q5: Late Delivery by Region** *(Basic — SUM GROUP BY)*")
        df5 = run_query("""
            SELECT [Order Region]                                           AS Region,
                   ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)    AS Late_Rate_Pct,
                   COUNT(*)                                                 AS Orders
            FROM supply_chain_orders
            GROUP BY Region
            ORDER BY Late_Rate_Pct DESC
        """)
        fig5 = px.bar(df5, x='Late_Rate_Pct', y='Region',
                      orientation='h', color='Late_Rate_Pct',
                      color_continuous_scale='Reds',
                      title='Late Delivery Rate by Region (%)',
                      text='Late_Rate_Pct')
        fig5.update_traces(texttemplate='%{text}%', textposition='outside')
        fig5.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        st.markdown("**Q6: Revenue by Category** *(Basic — SUM AVG)*")
        df6 = run_query("""
            SELECT [Category Name]                                          AS Category,
                   ROUND(SUM(Sales), 0)                                     AS Revenue,
                   ROUND(AVG([Order Item Profit Ratio]) * 100, 1)           AS Margin
            FROM supply_chain_orders
            GROUP BY Category
            ORDER BY Revenue DESC
            LIMIT 12
        """)
        fig6 = px.bar(df6, x='Revenue', y='Category',
                      orientation='h', color='Margin',
                      color_continuous_scale='Blues',
                      title='Revenue by Category (colour = margin %)')
        fig6.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown("**Q7: Monthly Revenue Trend** *(Intermediate — DATE functions)*")
    df7 = run_query("""
        SELECT SUBSTR([order date (DateOrders)], 1, 7)  AS Month,
               ROUND(SUM(Sales), 0)                     AS Revenue,
               COUNT(*)                                 AS Orders
        FROM supply_chain_orders
        WHERE [order date (DateOrders)] IS NOT NULL
        GROUP BY Month
        ORDER BY Month
    """)
    fig7 = px.line(df7, x='Month', y='Revenue',
                   title='Monthly Revenue Trend',
                   markers=True,
                   color_discrete_sequence=['#0F6E56'])
    fig7.update_layout(height=380, xaxis_tickangle=-45)
    st.plotly_chart(fig7, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Q8: Shipping Mode Performance** *(Intermediate — CASE WHEN rating)*")
        df8 = run_query("""
            SELECT [Shipping Mode]                                                  AS Mode,
                   COUNT(*)                                                         AS Orders,
                   ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)            AS Late_Rate,
                   CASE
                       WHEN SUM(Late_delivery_risk) * 100.0 / COUNT(*) > 60 THEN 'Critical'
                       WHEN SUM(Late_delivery_risk) * 100.0 / COUNT(*) > 40 THEN 'Poor'
                       ELSE 'Acceptable'
                   END                                                              AS Rating
            FROM supply_chain_orders
            GROUP BY Mode
            ORDER BY Late_Rate DESC
        """)
        st.dataframe(df8, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("**Q9: Customer Segment Analysis** *(Intermediate)*")
        df9 = run_query("""
            SELECT [Customer Segment]                       AS Segment,
                   ROUND(SUM(Sales), 0)                     AS Revenue,
                   COUNT(DISTINCT [Customer Id])            AS Customers
            FROM supply_chain_orders
            GROUP BY Segment
        """)
        fig9 = px.pie(df9, values='Revenue', names='Segment',
                      title='Revenue by Customer Segment', hole=0.4)
        st.plotly_chart(fig9, use_container_width=True)

# ── TAB 3: WINDOW FUNCTIONS ──────────────────────────────────────
with tab3:
    st.subheader("Advanced Window Functions")
    st.markdown("*RANK · DENSE_RANK · ROW_NUMBER · LAG · LEAD · Running Totals · Moving Averages*")

    st.markdown("**Q10: Revenue Ranking by Region** *(Advanced — RANK DENSE_RANK ROW_NUMBER)*")
    df10 = run_query("""
        WITH region_summary AS (
            SELECT [Order Region]           AS Region,
                   Market,
                   ROUND(SUM(Sales), 0)     AS Revenue,
                   COUNT(*)                 AS Orders
            FROM supply_chain_orders
            GROUP BY Region, Market
        )
        SELECT Region, Market, Revenue, Orders,
               RANK()       OVER (ORDER BY Revenue DESC) AS Rank,
               DENSE_RANK() OVER (ORDER BY Revenue DESC) AS Dense_Rank,
               ROW_NUMBER() OVER (ORDER BY Revenue DESC) AS Row_Num
        FROM region_summary
        ORDER BY Rank
        LIMIT 15
    """)
    st.dataframe(df10, hide_index=True, use_container_width=True)
    st.info("RANK skips numbers after ties. DENSE_RANK does not skip. ROW_NUMBER is always unique.")

    st.markdown("**Q11: Month over Month Trend** *(Advanced — LAG LEAD)*")
    df11 = run_query("""
        WITH monthly AS (
            SELECT SUBSTR([order date (DateOrders)], 1, 7)  AS Month,
                   ROUND(SUM(Sales), 0)                     AS Revenue
            FROM supply_chain_orders
            WHERE [order date (DateOrders)] IS NOT NULL
            GROUP BY Month
        )
        SELECT Month,
               Revenue,
               LAG(Revenue)  OVER (ORDER BY Month)  AS Prev_Revenue,
               LEAD(Revenue) OVER (ORDER BY Month)  AS Next_Revenue,
               ROUND((Revenue - LAG(Revenue) OVER (ORDER BY Month)) * 100.0 /
                     NULLIF(LAG(Revenue) OVER (ORDER BY Month), 0), 1)  AS MoM_Change_Pct,
               CASE
                   WHEN Revenue > LAG(Revenue) OVER (ORDER BY Month) THEN 'Growing'
                   WHEN Revenue < LAG(Revenue) OVER (ORDER BY Month) THEN 'Declining'
                   ELSE 'Stable'
               END AS Trend
        FROM monthly
        ORDER BY Month
        LIMIT 24
    """)
    fig11 = px.line(df11, x='Month', y='Revenue',
                    title='Revenue with LAG/LEAD Trend Analysis',
                    color_discrete_sequence=['#185FA5'],
                    markers=True)
    fig11.update_layout(height=350, xaxis_tickangle=-45)
    st.plotly_chart(fig11, use_container_width=True)
    st.dataframe(df11.head(12), hide_index=True, use_container_width=True)

    st.markdown("**Q12: Cumulative Revenue + 3-Month Moving Average** *(Advanced — Running window)*")
    df12 = run_query("""
        WITH monthly AS (
            SELECT SUBSTR([order date (DateOrders)], 1, 7)  AS Month,
                   ROUND(SUM(Sales), 0)                     AS Revenue
            FROM supply_chain_orders
            WHERE [order date (DateOrders)] IS NOT NULL
            GROUP BY Month
        )
        SELECT Month,
               Revenue,
               SUM(Revenue) OVER (ORDER BY Month
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)    AS Cumulative,
               ROUND(AVG(Revenue) OVER (ORDER BY Month
                   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0)        AS Moving_Avg_3M
        FROM monthly
        ORDER BY Month
        LIMIT 24
    """)
    fig12 = px.line(df12, x='Month', y=['Revenue', 'Moving_Avg_3M'],
                    title='Revenue vs 3-Month Moving Average')
    fig12.update_layout(height=350, xaxis_tickangle=-45)
    st.plotly_chart(fig12, use_container_width=True)

    st.markdown("**Q13: ABC Inventory Classification** *(Advanced — CTE cumulative %)*")
    df13 = run_query("""
        WITH prod AS (
            SELECT [Product Name]           AS Product,
                   ROUND(SUM(Sales), 0)     AS Revenue,
                   COUNT(*)                 AS Orders
            FROM supply_chain_orders
            GROUP BY Product
            ORDER BY Revenue DESC
        ),
        cum AS (
            SELECT Product, Revenue, Orders,
                   ROUND(SUM(Revenue) OVER (
                       ORDER BY Revenue DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                   ) * 100.0 / SUM(Revenue) OVER (), 1)     AS Cum_Pct
            FROM prod
        )
        SELECT Product, Revenue, Orders, Cum_Pct,
               CASE
                   WHEN Cum_Pct <= 80 THEN 'A — Top 80%'
                   WHEN Cum_Pct <= 95 THEN 'B — Middle 15%'
                   ELSE                    'C — Bottom 5%'
               END AS ABC_Class
        FROM cum
        ORDER BY Revenue DESC
        LIMIT 20
    """)
    col1, col2 = st.columns(2)
    with col1:
        abc_summary = df13.groupby('ABC_Class')['Revenue'].sum().reset_index()
        fig13 = px.bar(abc_summary, x='ABC_Class', y='Revenue',
                       color='ABC_Class', title='Revenue by ABC Class',
                       color_discrete_map={
                           'A — Top 80%':    '#0F6E56',
                           'B — Middle 15%': '#185FA5',
                           'C — Bottom 5%':  '#A32D2D'
                       })
        st.plotly_chart(fig13, use_container_width=True)
    with col2:
        st.dataframe(df13[['Product', 'Revenue', 'ABC_Class']].head(15),
                     hide_index=True, use_container_width=True)

# ── TAB 4: CROSS DOMAIN ──────────────────────────────────────────
with tab4:
    st.subheader("Cross Domain Analysis")
    st.markdown("*Combining healthcare and supply chain insights in a single view*")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Healthcare Executive KPI Summary**")
        hc_exec = run_query("""
            SELECT COUNT(DISTINCT Rndrng_NPI)                       AS Total_Providers,
                   COUNT(DISTINCT Rndrng_Prvdr_Type)                AS Specialties,
                   SUM(Tot_Benes)                                   AS Total_Patients,
                   ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 0)    AS Total_Revenue,
                   ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2)                AS Avg_Payment
            FROM healthcare_providers
        """)
        if not hc_exec.empty:
            for col, val in hc_exec.iloc[0].items():
                label = col.replace('_', ' ')
                st.metric(label, f"{val:,.0f}" if isinstance(val, float) and val > 100 else val)

    with col2:
        st.markdown("**Supply Chain Executive KPI Summary**")
        sc_exec = run_query("""
            SELECT COUNT(*)                                                 AS Total_Orders,
                   COUNT(DISTINCT [Customer Id])                            AS Customers,
                   ROUND(SUM(Sales), 0)                                     AS Total_Revenue,
                   ROUND(SUM([Order Profit Per Order]), 0)                  AS Total_Profit,
                   ROUND(SUM(Late_delivery_risk) * 100.0 / COUNT(*), 1)    AS Late_Rate_Pct
            FROM supply_chain_orders
        """)
        if not sc_exec.empty:
            for col, val in sc_exec.iloc[0].items():
                label = col.replace('_', ' ')
                st.metric(label, f"{val:,.1f}" if isinstance(val, float) else f"{val:,}")

    st.markdown("**Q14: Top States — Healthcare Revenue vs Supply Chain Orders** *(Advanced — Two CTEs + JOIN)*")
    df_cross = run_query("""
        WITH hc AS (
            SELECT Rndrng_Prvdr_State_Abrvtn                                        AS State,
                   ROUND(SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs), 0)                    AS HC_Revenue,
                   COUNT(DISTINCT Rndrng_NPI)                                       AS Providers,
                   RANK() OVER (ORDER BY SUM(Avg_Mdcr_Pymt_Amt * Tot_Srvcs) DESC)  AS HC_Rank
            FROM healthcare_providers
            GROUP BY State
        ),
        sc AS (
            SELECT [Customer State]             AS State,
                   ROUND(SUM(Sales), 0)         AS SC_Revenue,
                   COUNT(*)                     AS SC_Orders
            FROM supply_chain_orders
            WHERE [Customer State] IS NOT NULL
            GROUP BY State
        )
        SELECT h.State, h.HC_Revenue, h.Providers,
               h.HC_Rank AS Healthcare_Rank,
               s.SC_Revenue, s.SC_Orders
        FROM hc h
        LEFT JOIN sc s ON h.State = s.State
        WHERE h.HC_Rank <= 15
        ORDER BY h.HC_Rank
    """)
    st.dataframe(df_cross, hide_index=True, use_container_width=True)
    st.caption("Two CTEs joined across different real-world datasets — a common pattern in enterprise analytics.")

# ── TAB 5: SQL EXPLORER ──────────────────────────────────────────
with tab5:
    st.subheader("🔍 Live SQL Query Explorer")
    st.markdown("Write and run any SQL query against the real in-memory database.")

    table_choice = st.radio(
        "Select table:",
        ["healthcare_providers", "supply_chain_orders"],
        horizontal=True
    )

    sample_queries = {
        "healthcare_providers": """SELECT Rndrng_Prvdr_Type       AS Specialty,
       COUNT(DISTINCT Rndrng_NPI)  AS Providers,
       ROUND(AVG(Avg_Mdcr_Pymt_Amt), 2) AS Avg_Payment
FROM healthcare_providers
GROUP BY Specialty
ORDER BY Avg_Payment DESC
LIMIT 10""",
        "supply_chain_orders": """SELECT [Order Region]                                        AS Region,
       COUNT(*)                                              AS Orders,
       ROUND(SUM(Sales), 2)                                  AS Revenue,
       ROUND(SUM(Late_delivery_risk)*100.0/COUNT(*), 1)      AS Late_Pct
FROM supply_chain_orders
GROUP BY Region
ORDER BY Revenue DESC"""
    }

    user_query = st.text_area(
        "Enter SQL query:",
        value=sample_queries[table_choice],
        height=160
    )

    if st.button("▶ Run Query", type="primary"):
        try:
            result = run_query(user_query)
            if result.empty:
                st.warning("Query ran successfully but returned no rows.")
            else:
                st.success(f"✅ Query returned {len(result):,} rows")
                st.dataframe(result, hide_index=True, use_container_width=True)
                num_cols = result.select_dtypes(include='number').columns.tolist()
                str_cols = result.select_dtypes(include='object').columns.tolist()
                if num_cols and str_cols:
                    fig = px.bar(result.head(20),
                                 x=num_cols[0], y=str_cols[0],
                                 orientation='h',
                                 title='Query Result Visualisation')
                    fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Error: {e}")

    st.markdown("---")
    st.markdown("**Browse Pre-run Query Results**")
    output_dir = 'outputs/sql'
    if os.path.exists(output_dir):
        sql_files = [f for f in os.listdir(output_dir)
                     if f.endswith('.csv') and f != '00_QUERY_SUMMARY.csv']
        if sql_files:
            selected_file = st.selectbox("Select query result:", sorted(sql_files))
            if selected_file:
                df_selected = pd.read_csv(f'{output_dir}/{selected_file}')
                st.caption(f"{len(df_selected):,} rows")
                st.dataframe(df_selected, hide_index=True, use_container_width=True)
        else:
            st.info("No pre-run query files found in outputs/sql/")
    else:
        st.info("outputs/sql/ folder not found — run your SQL export script first.")

# ── FOOTER ───────────────────────────────────────────────────────
st.divider()
st.markdown(
    "**Datasets:** CMS Medicare Provider Data 2022 + DataCo Supply Chain &nbsp;|&nbsp; "
    "**Built by:** Karan Trivedi · MS Data Analytics, Webster University &nbsp;|&nbsp; "
    "**SQL Coverage:** Basic · Intermediate · Advanced Window Functions · CTEs · Subqueries &nbsp;|&nbsp; "
    "**Tools:** SQL · SQLite · Python · Plotly · Streamlit"
)
