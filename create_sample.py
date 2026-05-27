import pandas as pd
import sqlite3

# Load existing CSVs
hc = pd.read_csv('data/cms_healthcare.csv', low_memory=False)
sc = pd.read_csv('data/supply_chain.csv', encoding='latin-1',
                 low_memory=False)

# Create cloud database with full sample
conn = sqlite3.connect('business_analytics_cloud.db')
hc.to_sql('healthcare_providers', conn,
          if_exists='replace', index=False)
sc.to_sql('supply_chain_orders', conn,
          if_exists='replace', index=False)
conn.close()
print(f"Cloud database created")
print(f"Healthcare: {len(hc):,} rows")
print(f"Supply chain: {len(sc):,} rows")