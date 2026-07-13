import numpy as np
import pandas as pd

df = pd.read_csv(r"C:\Users\User\Desktop\cleaned_online_data.csv") # read my cleaned data from my desktop
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"]) # analyze the datetime column to enable temporal feature extraction
df['Hour'] = df['InvoiceDate'].dt.hour # extract the integer hour (0-23) from the timestamp to isolate daily transaction patterns
hourly_transactions = df['Hour'].value_counts().sort_index() # aggregate and rank transactions by hour to identify operational bounds

# printing this distribution reveals that transaction volumes materialize at 06:00 (1 transaction),
# scale rapidly throughout the day, and drop off sharply by 20:00 (778 transactions), confirming
# a definitive 6:00 AM – 8:00 PM operational trading window.
print(hourly_transactions)


#SALES VELOCITY CURATION
#  Filter for UK and group by SKU, Date, and Hour to get hourly sums
df_uk = df[df['Country'] == 'United Kingdom'].copy()
df_uk['Hour'] = pd.to_datetime(df_uk['InvoiceDate']).dt.hour
df_uk['Date'] = pd.to_datetime(df_uk['InvoiceDate']).dt.date

# Calculate the mean hourly volume for EVERY product
sku_velocities = (
    df_uk.groupby(['StockCode', 'Description', 'Date', 'Hour'])['Quantity']
    .sum()
    .groupby(level=['StockCode', 'Description'])
    .mean()
    .reset_index(name='Velocity')
)

# Query for products matching specified conditions
high_vol = sku_velocities[sku_velocities['Velocity'] > 28].head(2)
med_vol  = sku_velocities[(sku_velocities['Velocity'] > 5) & (sku_velocities['Velocity'] < 10)].head(2)
low_vol  = sku_velocities[(sku_velocities['Velocity'] >= 0.9) & (sku_velocities['Velocity'] <= 1.2)].head(2)

# Combine and print out the SKUs
catalog_df = pd.concat([high_vol, med_vol, low_vol])
print(catalog_df.to_string(index=False))