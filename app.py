
import streamlit as st # Note: Standard naming convention is import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson


st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

# PRODUCTION-GRADE DATA PIPELINE (Poisson Compliant)
@st.cache_data
def load_sku_catalog():
    # 1. Read dataset
    df = pd.read_csv("cleaned_online_data.zip")
    
    # 2. Filter for UK market consistency
    df_uk = df[df['Country'] == 'United Kingdom'].copy()
    df_uk['InvoiceDate'] = pd.to_datetime(df_uk['InvoiceDate'])
    
    # 3. Define the total temporal footprint of your data window
    df_uk['Date'] = df_uk['InvoiceDate'].dt.date
    df_uk['Hour'] = df_uk['InvoiceDate'].dt.hour
    
    total_active_hours = df_uk.groupby(['Date', 'Hour']).ngroups or 1

    # 4. Aggregate total units sold per SKU
    catalog_df = (
        df_uk.groupby("StockCode")
        .agg(
            Description=("Description", "first"),
            Total_Units=("Quantity", "sum")
        )
    )
    
    # 5. Calculate true statistical velocity and enforce a realistic minimum
    raw_velocity = catalog_df['Total_Units'] / total_active_hours
    catalog_df['Calculated_Velocity'] = np.maximum(0.2, raw_velocity)
    
    # Sort for better UX in the full catalogue
    catalog_df = catalog_df.sort_values(by='Calculated_Velocity', ascending=False)
    
    return catalog_df.to_dict("index")

# Curated list for the default view
curated_skus = {
    "22439": {"Description": "6 ROCKET BALLON", "Calculated_Velocity": 0.59},
    "22046": {"Description": "TEA WRAPING PAPER", "Calculated_Velocity": 0.59},
    "22713": {"Description": "CARD I LOVE LONDON", "Calculated_Velocity": 1.13},
    "17003": {"Description": "BROCADE RING PURSE", "Calculated_Velocity": 8.04},
    "90062": {"Description": "CARNIVAL BRACELET", "Calculated_Velocity": 0.20},
    "22670": {"Description": "FRENCH WC SIGN BLUE METAL", "Calculated_Velocity": 0.53}
}

# Load the catalog once
full_catalog = load_sku_catalog()

# SIDEBAR CONTROLS 

st.sidebar.header(" Simulation Controls")
show_all = st.sidebar.checkbox("Explore Full Catalogue")
full_catalog = load_sku_catalog()
sku_catalog = full_catalog if show_all else curated_skus

selected_sku = st.sidebar.selectbox(
    "Select Target Product", 
    options=list(sku_catalog.keys()),
    index=4, # Defaults to 20663
    format_func=lambda x: f"{x} — {sku_catalog[x]['Description']}"
)

default_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")

normal_velocity = st.sidebar.slider(
    "Normal Sales Velocity (Units/Hour)", 
    min_value=0.1, 
    max_value=max(20.0, float(default_velocity) * 1.5), 
    value=float(default_velocity), 
    step=0.1,
    key=f"vel_{selected_sku}"
)

hours_zero_sales = st.sidebar.slider(
    "Current Hours with Zero Sales", 
    min_value=1, 
    max_value=24, 
    value=3, 
    step=1,
    key=f"hrs_{selected_sku}"
)
confidence_threshold = st.sidebar.slider(
    "Alert Sensitivity(%)", 
    min_value=80, 
    max_value=99, 
    value=95, 
    step=1,
    key="sensitivity_slider"
)

# POISSON DISTRIBUTION

expected_sales_in_window = normal_velocity * hours_zero_sales
prob_of_slow_gap = poisson.pmf(0, expected_sales_in_window)
phantom_stock_confidence = (1 - prob_of_slow_gap) * 100

# MAIN DASHBOARD VISUAL OUTPUT

st.title("Inventory Intelligence Dashboard")
st.markdown(f"**Analyzing Core Inventory Stream** | Selected Item: `{selected_sku}` - *{product_desc}*")
st.markdown("---")

# Layout: 3 Columns for Summary Data
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Time Without Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sale", f"{expected_sales_in_window:.1f} units")

st.markdown("### Anomaly Assessment")

# Dynamic KPI Alert Card with 3 Tiers (Critical, Warning, Normal)
if phantom_stock_confidence >= confidence_threshold:
    st.error(f"""
    ### CRITICAL: PHANTOM INVENTORY SUSPECTED ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** This product has been dry for {hours_zero_sales} hours. Statistically, there is only a 
    {prob_of_slow_gap*100:.2f}% chance this is a natural sales slump. The item is likely missing, stolen, or misplaced. 
    A task has been dispatched to floor staff to physically audit the shelf location.
    """)
elif phantom_stock_confidence >= (confidence_threshold - 15):
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** The item is approaching the alert threshold. Sales are unusually slow, but still within 
    marginal statistical variance. The system will continue to monitor before dispatching staff.
    """)
else:
    st.success(f"""
    ###  STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** The current {hours_zero_sales}-hour sales gap falls completely within expected normal statistical variance 
    for an item selling at {normal_velocity:.1f} units/hr. No operational response required.
    """)

# 5. OPERATIONAL OUTPUT (Dynamic Staff Worklist)

import hashlib

st.markdown("---")
st.markdown("###  Automated Floor Staff Worklist")
st.markdown("This table acts as a 'System of Action', dynamically feeding prioritized tasks directly to staff PDA terminals based on real-time data.")

# Helper function to generate consistent pseudo-random aisle locations based on the SKU
def get_mock_location(sku_str):
    hash_val = int(hashlib.md5(str(sku_str).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"

# Get the currently selected SKU and grab neighboring items to build a 100% dynamic list
sku_list = list(sku_catalog.keys())
selected_idx = sku_list.index(selected_sku)

# Select 3 items: the target item + 2 other real items from the catalog
simulated_skus = [
    selected_sku,
    sku_list[(selected_idx + 1) % len(sku_list)],
    sku_list[(selected_idx + 2) % len(sku_list)]
]

worklist_data = []
for i, sku in enumerate(simulated_skus):
    # Apply the user's slider velocity to the main item; use pure data for the other two
    vel = normal_velocity if i == 0 else sku_catalog[sku]["Calculated_Velocity"]
    
    # Calculate Poisson confidence dynamically for each row
    exp_sales = vel * hours_zero_sales
    prob_zero = poisson.pmf(0, exp_sales)
    conf = (1 - prob_zero) * 100
    
    # Assign Priority Tiers matching the Engine Status logic
    if conf >= confidence_threshold:
        tier = "CRITICAL"
    elif conf >= (confidence_threshold - 15):
        tier = "WARNING"
    else:
        tier = "MONITOR"

    worklist_data.append({
        "Task ID": f"TSK-{9400 + selected_idx + i}",
        "SKU": sku,
        "Description": sku_catalog[sku]["Description"],
        "Aisle Location": get_mock_location(sku),
        "Anomaly Confidence": f"{conf:.1f}%",
        "Priority Tier": tier
    })

worklist_df = pd.DataFrame(worklist_data)

# Render the interactive dataframe table inside the app
st.dataframe(worklist_df, use_container_width=True, hide_index=True)
