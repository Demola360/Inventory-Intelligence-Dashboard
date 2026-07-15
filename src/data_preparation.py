"""
=============================================================================
PHANTOM STOCK DETECTOR — DATA PREPARATION PIPELINE
=============================================================================
Author: Ademola Salako
Dataset: UCI Online Retail Dataset (publicly available)
Source: https://archive.ics.uci.edu/dataset/352/online+retail

PURPOSE OF THIS SCRIPT
-----------------------
The raw dataset (Online Retail.xlsx) is ~45MB — too large to host on GitHub
and too slow to load inside a web application at runtime.

This script runs the full preparation workflow that was used to produce the
lightweight file (aggregated_catalog.csv) that the dashboard actually reads.

Steps performed:
    1. Load the raw data and inspect it (df.head / df.info)
    2. Identify and fix data quality issues found during that inspection
    3. Verify the fixes with a second df.info check
    4. Filter to United Kingdom only, then restrict to real trading hours
    5. Aggregate from ~350,000 transaction rows to one row per product (SKU)
    6. Save the compact output file for the dashboard to consume
=============================================================================
"""

import numpy as np
import pandas as pd


# =============================================================================
# STEP 1 — LOAD AND INSPECT THE RAW DATA
# =============================================================================
# Raw source: UCI Online Retail Dataset
# https://archive.ics.uci.edu/dataset/352/online+retail
# Download "Online Retail.xlsx" and place it in data/raw/ before running this script.

df = pd.read_excel("../data/raw/Online Retail.xlsx")

print("\n--- df.head() — first look at the raw data ---")
print(df.head().to_string())

print("\n--- df.info() — column types and missing value counts ---")
print(df.info())

# df.info() revealed three issues that needed fixing before any analysis:
#
#   1. CustomerID arrived as float64 because pandas uses NaN for missing values,
#      and NaN is a float — forcing the whole column into float64.
#
#   2. 135,080 rows have no CustomerID — unverifiable transactions that
#      shouldn't count toward a product's sales velocity.
#
#   3. Negative Quantity values are cancellations and returns, not real sales —
#      leaving them in would artificially deflate velocity calculations.


# =============================================================================
# STEP 2 — CLEAN THE DATA
# =============================================================================
print("\n\nCleaning data...")

df = df.drop_duplicates()
df = df.dropna(subset=['CustomerID'])

# Exclude cancellations (negative quantity) and internal adjustment rows
# (zero or negative price) — neither represents a real customer sale.
df = df[df['Quantity'] > 0]
df = df[df['UnitPrice'] > 0]

df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# Safe to cast to int now — all NaN rows were dropped in the step above.
df['CustomerID'] = df['CustomerID'].astype(int).astype(str)


# =============================================================================
# STEP 3 — VERIFY THE FIXES
# =============================================================================
# Running df.info() a second time rather than assuming the cleaning worked.
# Deliberate check: row count should drop from 541,909 to ~392,692,
# CustomerID should show no nulls, and dtype should now be object (string).

print("\n--- df.info() after cleaning — verifying fixes ---")
print(df.info())

print(f"\nRows remaining after cleaning: {len(df):,}")
print(f"CustomerID nulls remaining: {df['CustomerID'].isnull().sum()}")
print(f"Sample CustomerID value: {df['CustomerID'].iloc[0]}  (no trailing .0)")


# =============================================================================
# STEP 4 — FILTER TO UNITED KINGDOM AND RESTRICT TO TRADING HOURS
# =============================================================================
# The dataset spans 38 countries. Filtering to UK only lets us treat this
# as a single consistent store branch without needing to model country-level
# differences in demand patterns.

print("\n\nFiltering to United Kingdom transactions...")
df_uk = df[df['Country'] == 'United Kingdom'].copy()
print(f"UK rows: {len(df_uk):,}")

df_uk['Hour'] = df_uk['InvoiceDate'].dt.hour

# Inspecting the hour distribution showed virtually all transactions fall
# between 6am and 8pm — anything outside that window is almost certainly
# automated system entries, not real customer purchases.
#
# This filtering decision directly affects the Poisson model's accuracy:
# velocity = total units / total hours. If 3am counts in the denominator,
# the rate gets artificially diluted — making a product look slower than
# it actually is during real trading hours.

print("\nFiltering to trading hours (6am to 8pm)...")
df_trading = df_uk[
    (df_uk['Hour'] >= 6) &
    (df_uk['Hour'] < 20)
].copy()

total_trading_days      = df_trading['InvoiceDate'].dt.date.nunique()
hours_per_trading_day   = 14   # 6am to 8pm = 14 hours, empirically derived from the data
total_operational_hours = total_trading_days * hours_per_trading_day

print(f"Unique trading days in dataset: {total_trading_days}")
print(f"Total operational hours (denominator): {total_operational_hours}")


# =============================================================================
# STEP 5 — AGGREGATE TO ONE ROW PER PRODUCT (SKU)
# =============================================================================
# The dashboard only needs one number per product — its average sales rate.
# Collapsing ~350,000 transaction rows to one row per SKU reduces the file
# from 45MB to a few hundred KB, making it practical to ship with the app.

print("\n\nAggregating to product-level catalog...")

catalog_df = (
    df_trading.groupby("StockCode")
    .agg(
        Description=("Description", "first"),
        Total_Units=("Quantity", "sum")
    )
)

# Core velocity formula: units sold ÷ total operational hours.
# This is the lambda (λ) the Poisson model uses as its "normal" baseline.
raw_velocity = catalog_df['Total_Units'] / total_operational_hours

# Floor of 0.2 units/hour applied to very slow-moving products.
# Without it, a near-zero velocity means the model would never flag that
# product — even 24 hours of silence would look statistically normal.
# The floor keeps the anomaly detection meaningful across the full catalogue.
catalog_df['Calculated_Velocity'] = np.maximum(0.2, raw_velocity)

catalog_df = catalog_df.sort_values(by='Calculated_Velocity', ascending=False)

# Drop SKUs with no readable description — these are system or test entries,
# not real products a store would stock.
catalog_df = catalog_df.dropna()

print(f"Unique products in output catalog: {len(catalog_df):,}")


# =============================================================================
# STEP 6 — SAVE THE OUTPUT FILE
# =============================================================================
# This is the only file the Streamlit dashboard reads at runtime.
# The original 45MB Excel file is never committed to GitHub.

output_path = "../data/aggregated_catalog.csv"
catalog_df.to_csv(output_path)

print(f"\nSaved {len(catalog_df):,} products to '{output_path}'.")
print("Pipeline complete.")
