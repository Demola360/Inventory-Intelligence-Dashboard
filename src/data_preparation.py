"""
Phantom Stock Detector — Data Preparation Pipeline
----------------------------------------------------
Produces aggregated_catalog.csv from the raw UCI Online Retail dataset.
The raw file (~45MB) is too large to ship with the app, so this script
collapses ~350,000 transaction rows into one velocity figure per product.

Run this once locally, then commit the output CSV to the repo.
Raw data: https://archive.ics.uci.edu/dataset/352/online+retail
Place Online Retail.xlsx in data/raw/ before running.
"""

import numpy as np
import pandas as pd


# STEP 1 — LOAD AND INSPECT
df = pd.read_excel("../data/raw/Online Retail.xlsx")
print(df.head().to_string())
print(df.info())


# STEP 2 — CLEAN
# CustomerID arrived as float64 because NaN forces the column into float.
# Rows with no CustomerID are unverifiable — excluded from velocity calculation.
# Negative quantities are cancellations; negative prices are internal adjustments.
# Neither represents a real sale.
df = df.drop_duplicates()
df = df.dropna(subset=['CustomerID'])
df = df[df['Quantity'] > 0]
df = df[df['UnitPrice'] > 0]
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['CustomerID'] = df['CustomerID'].astype(int).astype(str)


# STEP 3 — VERIFY
# Row count should drop from 541,909 to ~392,692.
# CustomerID should show no nulls and dtype object (not float64).
print(df.info())
print(f"Rows after cleaning: {len(df):,}")


# STEP 4 — FILTER TO UK AND TRADING HOURS
# UK only — treats the dataset as a single consistent store branch.
# 06:00–20:00 only — empirically derived from the hour distribution
# (see notebooks/exploratory_analysis.ipynb). Including off-hours dilutes
# velocity by adding dead time to the denominator.
df_uk = df[df['Country'] == 'United Kingdom'].copy()
df_uk['Hour'] = df_uk['InvoiceDate'].dt.hour

df_trading = df_uk[
    (df_uk['Hour'] >= 6) &
    (df_uk['Hour'] < 20)
].copy()

total_trading_days = df_trading['InvoiceDate'].dt.date.nunique()
total_operational_hours = total_trading_days * 14  # 14-hour window

print(f"Trading days: {total_trading_days}")
print(f"Total operational hours: {total_operational_hours}")


# STEP 5 — AGGREGATE TO ONE ROW PER SKU
catalog_df = (
    df_trading.groupby("StockCode")
    .agg(
        Description=("Description", "first"),
        Total_Units=("Quantity", "sum")
    )
)

# velocity = units sold ÷ total operational hours — this is λ for the Poisson model
raw_velocity = catalog_df['Total_Units'] / total_operational_hours

# Floor at 0.2 — without it, near-zero velocity products would never flag,
# even after 24 hours of silence. At 0.2, Warning triggers at 9 hours and
# Critical at 15 hours at 95% sensitivity — within a single working shift.
catalog_df['Calculated_Velocity'] = np.maximum(0.2, raw_velocity)
catalog_df = catalog_df.sort_values(by='Calculated_Velocity', ascending=False)
catalog_df = catalog_df.dropna()

print(f"Products in output: {len(catalog_df):,}")


# STEP 6 — SAVE
output_path = "../data/aggregated_catalog.csv"
catalog_df.to_csv(output_path)
print(f"Saved to {output_path}. Pipeline complete.")
