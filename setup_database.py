import pandas as pd
import sqlite3
import os

print("="*55)
print("SQL BUSINESS ANALYTICS - DATABASE SETUP")
print("="*55)

# Connect to SQLite database
conn = sqlite3.connect('business_analytics.db')
print("Database created: business_analytics.db")

# Load Healthcare CMS data
print("\nLoading healthcare data...")
healthcare = pd.read_csv('data/cms_healthcare.csv', low_memory=False)
healthcare.to_sql('healthcare_providers', conn,
                  if_exists='replace', index=False)
print(f"healthcare_providers table: {len(healthcare):,} rows x {healthcare.shape[1]} columns")

# Load Supply Chain data
print("\nLoading supply chain data...")
supply = pd.read_csv('data/supply_chain.csv',
                     encoding='latin-1', low_memory=False)
supply.to_sql('supply_chain_orders', conn,
              if_exists='replace', index=False)
print(f"supply_chain_orders table: {len(supply):,} rows x {supply.shape[1]} columns")

# Verify both tables exist
print("\nVerifying database tables...")
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(f"Tables in database: {tables['name'].tolist()}")

# Quick column check
print("\nHealthcare columns:")
hc_cols = pd.read_sql("PRAGMA table_info(healthcare_providers)", conn)
for col in hc_cols['name'].tolist():
    print(f"  - {col}")

print("\nSupply chain columns:")
sc_cols = pd.read_sql("PRAGMA table_info(supply_chain_orders)", conn)
for col in sc_cols['name'].tolist():
    print(f"  - {col}")

conn.close()
print("\nDatabase setup complete. Ready for SQL queries.")