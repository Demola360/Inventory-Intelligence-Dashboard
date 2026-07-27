"""
Inventory Intelligence Dashboard, Data Preparation Pipeline
----------------------------------------------------
Produces aggregated_catalog.csv from the raw UCI Online Retail dataset.
The raw file (~45MB) is too large to ship with the app, so this script
collapses ~350,000 transaction rows into one velocity figure per product.

Run this once locally, then commit the output CSV to the repo.
Raw data: https://archive.ics.uci.edu/dataset/352/online+retail
Place Online Retail.xlsx in data/raw/ before running.
See src/exploratory_analysis.ipynb for the analysis behind these decisions.
"""

import numpy as np
import pandas as pd


# STEP 1, LOAD AND INSPECT
df = pd.read_excel("../data/raw/Online Retail.xlsx")
rows_start = len(df)
print(df.head().to_string())
print(df.info())


# STEP 2, CLEAN
# Each rule below is an analytical choice made for this POC, not a claim
# about what the removed rows represent.
rows_before_dupes = len(df)
df = df.drop_duplicates()
rows_after_dupes = len(df)

# CustomerID is not required by the velocity calculation (only StockCode,
# Quantity and InvoiceDate are used). It was excluded here as a conservative
# data-quality choice carried over from an earlier cleaning pass, not
# because these rows are known to be invalid sales. This should be
# reassessed against the actual removed-row proportion before reuse.
rows_before_customerid = len(df)
df = df.dropna(subset=['CustomerID'])
rows_after_customerid = len(df)

# Negative quantities are cancellations, negative prices are refunds or
# adjustments. Both are excluded from the positive-sales baseline used to
# calculate velocity, they may still represent real inventory activity,
# just not the kind this baseline is measuring.
rows_before_qty = len(df)
df = df[df['Quantity'] > 0]
rows_after_qty = len(df)

rows_before_price = len(df)
df = df[df['UnitPrice'] > 0]
rows_after_price = len(df)

df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['CustomerID'] = df['CustomerID'].astype(int).astype(str)


# STEP 3, VERIFY, WITH A ROW-IMPACT SUMMARY
print(df.info())
print("\nCleaning impact summary:")
print(f"  Starting rows:                 {rows_start:,}")
print(f"  Removed as exact duplicates:   {rows_before_dupes - rows_after_dupes:,}")
print(f"  Removed for missing CustomerID: {rows_before_customerid - rows_after_customerid:,}")
print(f"  Removed for non-positive Quantity: {rows_before_qty - rows_after_qty:,}")
print(f"  Removed for non-positive UnitPrice: {rows_before_price - rows_after_price:,}")
print(f"  Rows after cleaning: {len(df):,}")


# STEP 4, FILTER TO UK FIRST, THEN CHECK TRADING HOURS ON THAT SUBSET
# POC assumption: UK transactions are treated as one fictional branch to
# create a single operating context for the simulation, not a claim that
# this reflects a real single-branch operation.
df_uk = df[df['Country'] == 'United Kingdom'].copy()
df_uk['Hour'] = df_uk['InvoiceDate'].dt.hour

hourly_transactions_uk = df_uk['Hour'].value_counts().sort_index()
print("\nUK-only hourly transaction distribution:")
print(hourly_transactions_uk)

# Activity is negligible before hour 6 and after hour 20, supporting a
# 06:00 inclusive to 20:00 exclusive simulation window, based on observed
# transaction activity, not confirmed store opening hours.
df_trading = df_uk[
    (df_uk['Hour'] >= 6) &
    (df_uk['Hour'] < 20)
].copy()

total_trading_days = df_trading['InvoiceDate'].dt.date.nunique()
total_operational_hours = total_trading_days * 14

print(f"\nTrading days: {total_trading_days}")
print(f"Total operational hours: {total_operational_hours}")


# STEP 5, REMOVE NON-PRODUCT STOCK CODES
# These codes were identified by manual inspection of the dataset's
# StockCode/Description pairs, not from an official UCI data dictionary.
# They represent administrative entries, not physical shelf products, so
# they're excluded from a shelf-check monitoring tool.
# BR: Administrative stock codes must be excluded from physical
# shelf-check monitoring.
NON_PRODUCT_CODES = ['POST', 'BANK CHARGES', 'DOT', 'D', 'M', 'C2', 'PADS', 'CRUK']
df_trading = df_trading[~df_trading['StockCode'].isin(NON_PRODUCT_CODES)].copy()


# STEP 6, AGGREGATE TO ONE ROW PER SKU
# Note: every SKU currently shares the same operational-hour denominator,
# calculated across the whole observation period. This assumes each
# product was available and sellable throughout that entire period. A
# product introduced or discontinued partway through would have its rate
# understated or overstated as a result. See docs/limitations.md.
catalog_df = (
    df_trading.groupby("StockCode")
    .agg(
        Description=("Description", "first"),
        Total_Units=("Quantity", "sum")
    )
)

raw_velocity = catalog_df['Total_Units'] / total_operational_hours

# MONITORING_VELOCITY_FLOOR is a deliberate business decision, not a
# statistical necessity: below this rate, a product would require a
# longer zero-sales interval to cross the demonstration alert thresholds
# than the POC is intended to simulate. This is separate from the true
# observed velocity, which is preserved below for transparency.
MONITORING_VELOCITY_FLOOR = 0.2

catalog_df['Observed_Velocity'] = raw_velocity
catalog_df['Monitoring_Velocity'] = np.maximum(MONITORING_VELOCITY_FLOOR, raw_velocity)
catalog_df = catalog_df.sort_values(by='Monitoring_Velocity', ascending=False)
catalog_df = catalog_df.dropna()

print(f"\nProducts in output: {len(catalog_df):,}")


# STEP 7, SAVE
output_path = "../data/aggregated_catalog.csv"
catalog_df.to_csv(output_path)
print(f"Saved to {output_path}. Pipeline complete.")
