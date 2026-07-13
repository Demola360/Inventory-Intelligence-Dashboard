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
# First thing: load the file and look at what we're working with.
# Raw source: UCI Online Retail Dataset
# https://archive.ics.uci.edu/dataset/352/online+retail
# Download "Online Retail.xlsx" and place it in data/raw/ before running this script
# df.head() shows the first few rows so we can see the structure and spot
# anything that looks immediately wrong. df.info() gives us column types,
# row counts, and — crucially — which columns have missing values.

df = pd.read_excel("data/raw/Online Retail.xlsx")

print("\n--- df.head() — first look at the raw data ---")
print(df.head().to_string())

print("\n--- df.info() — column types and missing value counts ---")
print(df.info())

# What df.info() revealed that needed fixing:
#
#   1. CustomerID is float64 (e.g. 17850.0) — it should be a clean string ('17850').
#      It arrived as a float because pandas uses NaN to represent missing values,
#      and NaN is a float type, which forced the whole column into float64.
#
#   2. CustomerID has 135,080 missing values out of 541,909 rows — those rows
#      have no customer attached to the transaction and cannot be verified as
#      legitimate sales.
#
#   3. There are negative Quantity values in the data — these are cancellations
#      or returns, not actual sales, and would corrupt velocity calculations.


# =============================================================================
# STEP 2 — CLEAN THE DATA
# =============================================================================
# Fixing everything identified above, plus a couple of standard hygiene steps.

print("\n\nCleaning data...")

# Remove exact duplicate rows — can occur when data is exported more than once
df = df.drop_duplicates()

# Drop rows with no CustomerID — unverifiable transactions
df = df.dropna(subset=['CustomerID'])

# Remove cancellations and returns (negative or zero quantities)
# and internal adjustment rows (zero or negative unit price)
df = df[df['Quantity'] > 0]
df = df[df['UnitPrice'] > 0]

# Parse InvoiceDate properly so we can extract hours and dates later
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# Fix the CustomerID type: float (17850.0) → int (17850) → string ('17850')
# We can safely cast to int now because we've already dropped all NaN rows
df['CustomerID'] = df['CustomerID'].astype(int).astype(str)


# =============================================================================
# STEP 3 — VERIFY THE FIXES WITH A SECOND df.info() CHECK
# =============================================================================
# After cleaning, run df.info() again to confirm the issues are resolved.
# This is how you know the cleaning actually worked rather than just assuming.

print("\n--- df.info() after cleaning — verifying fixes ---")
print(df.info())

# What to confirm here:
#   - Row count dropped from 541,909 to ~392,692 (missing + invalid rows removed)
#   - CustomerID is now object dtype (string), no nulls remaining
#   - Quantity and UnitPrice columns no longer contain negatives or zeros

print(f"\nRows remaining after cleaning: {len(df):,}")
print(f"CustomerID nulls remaining: {df['CustomerID'].isnull().sum()}")
print(f"Sample CustomerID value: {df['CustomerID'].iloc[0]}  (no trailing .0)")


# =============================================================================
# STEP 4 — FILTER TO UNITED KINGDOM AND RESTRICT TO TRADING HOURS
# =============================================================================
# The dataset spans 38 countries. For this project, UK transactions are treated
# as a single store branch — a deliberate simplification that gives a consistent
# sales pattern without needing to model cross-country differences.

print("\n\nFiltering to United Kingdom transactions...")
df_uk = df[df['Country'] == 'United Kingdom'].copy()
print(f"UK rows: {len(df_uk):,}")

# Extract the hour from each transaction timestamp
df_uk['Hour'] = df_uk['InvoiceDate'].dt.hour

# Inspecting the hour distribution (done during exploration) showed that
# virtually all transactions fall between 6am and 8pm. Records outside
# that window are likely automated system entries, not real customer sales.
#
# This matters for the Poisson model: velocity = total units / total hours.
# If 3am counts in the denominator, the rate gets artificially diluted —
# a product selling 100 units across 14 real trading hours looks like it
# sold 100 units across 24 hours. Restricting to trading hours keeps
# the velocity calculation grounded in reality.

print("\nFiltering to trading hours (6am to 8pm)...")
df_trading = df_uk[
    (df_uk['Hour'] >= 6) &
    (df_uk['Hour'] < 20)
].copy()

total_trading_days     = df_trading['InvoiceDate'].dt.date.nunique()
hours_per_trading_day  = 14   # 6am to 8pm = 14 hours
total_operational_hours = total_trading_days * hours_per_trading_day

print(f"Unique trading days in dataset: {total_trading_days}")
print(f"Total operational hours (denominator): {total_operational_hours}")


# =============================================================================
# STEP 5 — AGGREGATE TO ONE ROW PER PRODUCT (SKU)
# =============================================================================
# The cleaned dataset still has ~350,000 individual transaction rows.
# The dashboard doesn't need that level of detail — it only needs to know
# how fast each product sells on average. So we collapse the data to one
# row per SKU, which reduces the file from 45MB to a few hundred KB.

print("\n\nAggregating to product-level catalog...")

catalog_df = (
    df_trading.groupby("StockCode")
    .agg(
        Description=("Description", "first"),  # one description per product
        Total_Units=("Quantity", "sum")         # total units sold in the full window
    )
)

# Velocity = how many units this product sells per operational hour on average.
# This becomes the "normal" baseline the Poisson model compares against.
raw_velocity = catalog_df['Total_Units'] / total_operational_hours

# Apply a minimum floor of 0.2 units/hour.
# A product with a true velocity near zero would essentially never trigger an
# alert — even 24 hours of silence would look statistically normal. The floor
# ensures the model stays meaningful for any product that is actually stocked.
catalog_df['Calculated_Velocity'] = np.maximum(0.2, raw_velocity)

# Sort fastest to slowest — useful when browsing the full catalog in the dashboard
catalog_df = catalog_df.sort_values(by='Calculated_Velocity', ascending=False)

# Drop any rows where the description is missing (a small number of
# system-generated or test SKUs that have no readable product name)
catalog_df = catalog_df.dropna()

print(f"Unique products in output catalog: {len(catalog_df):,}")


# =============================================================================
# STEP 6 — SAVE THE OUTPUT FILE
# =============================================================================
# This is the file the Streamlit dashboard reads at runtime.
# The original Excel file is never uploaded to GitHub.

output_path = "aggregated_catalog.csv"
catalog_df.to_csv(output_path)

print(f"\nSaved {len(catalog_df):,} products to '{output_path}'.")
print("Pipeline complete.")
