import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import hashlib

st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

# DATA PIPELINE 
@st.cache_data
def load_sku_catalog():
    # Read the light, pre-aggregated file (Fixes BadZipFile completely)
    df = pd.read_csv("aggregated_catalog.csv")
    
    # Set StockCode as string and index to match previous structure
    df['StockCode'] = df['StockCode'].astype(str)
    catalog_df = df.set_index('StockCode')
    
    return catalog_df.to_dict("index")

# Curated examples for the default view (hardcoded historical baselines)
curated_skus = {
    "22439": {"Description": "6 ROCKET BALLON", "Calculated_Velocity": 0.59},
    "22046": {"Description": "TEA WRAPPING PAPER", "Calculated_Velocity": 0.59},
    "22713": {"Description": "CARD I LOVE LONDON", "Calculated_Velocity": 1.13},
    "17003": {"Description": "BROCADE RING PURSE", "Calculated_Velocity": 8.04},
    "90062": {"Description": "CARNIVAL BRACELET", "Calculated_Velocity": 0.20},
    "22670": {"Description": "FRENCH WC SIGN BLUE METAL", "Calculated_Velocity": 0.53}
}

# Load data once at runtime
full_catalog = load_sku_catalog()

# SIDEBAR CONTROLS
st.sidebar.header("Simulation Controls")
show_all = st.sidebar.checkbox("Explore Full Catalogue")

# Corrected: Use full_catalog or curated_skus cleanly without double loading
sku_catalog = full_catalog if show_all else curated_skus

selected_sku = st.sidebar.selectbox(
    "Select Target Product", 
    options=list(sku_catalog.keys()),
    index=4, 
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

# POISSON DISTRIBUTION ENGINE
expected_sales_in_window = normal_velocity * hours_zero_sales
prob_of_slow_gap = poisson.pmf(0, expected_sales_in_window)
phantom_stock_confidence = (1 - prob_of_slow_gap) * 100

# MAIN DASHBOARD
st.title("Inventory Intelligence Dashboard")
st.markdown(f"**Analyzing Core Inventory Stream** | Selected Item: `{selected_sku}` - *{product_desc}*")

# Framework context for reviewers
with st.expander(" Methodology & Operational Boundaries (MVP Framework)"):
    st.markdown("""
    * **Why Poisson?** It requires minimal data overhead compared to heavy machine learning models, making it highly scalable for long-tail retail items.
    * **Operational Baseline:** Based on exploratory data analysis, transaction activity strictly occurs within a **14-hour daily window (06:00 - 20:00)**. Sales velocities are normalized against actual operational hours to prevent overnight false-positive alerts.
    """)

st.markdown("---")

# Key Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Time Without Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sale", f"{expected_sales_in_window:.1f} units")

st.markdown("### Anomaly Assessment")

# Dynamic Alert Thresholds
if phantom_stock_confidence >= confidence_threshold:
    st.error(f"""
    ### CRITICAL: PHANTOM INVENTORY SUSPECTED ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** This product has been dry for {hours_zero_sales} hours. Statistically, there is only a 
    {prob_of_slow_gap*100:.2f}% chance this is a natural sales slump. A task has been dispatched to floor staff to audit the shelf location.
    """)
elif phantom_stock_confidence >= (confidence_threshold - 15):
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** The item is approaching the alert threshold. Sales are unusually slow, but still within marginal statistical variance.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** The current {hours_zero_sales}-hour sales gap falls completely within expected normal statistical variance. No operational response required.
    """)

# OPERATIONAL OUTPUT (SYSTEM OF ACTION)
st.markdown("---")
st.markdown("### Automated Floor Staff Worklist")
st.markdown("This table acts as a 'System of Action', dynamically feeding prioritized tasks directly to staff PDA terminals based on real-time data.")

def get_mock_location(sku_str):
    hash_val = int(hashlib.md5(str(sku_str).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"

sku_list = list(sku_catalog.keys())
selected_idx = sku_list.index(selected_sku)
simulated_skus = [
    selected_sku,
    sku_list[(selected_idx + 1) % len(sku_list)],
    sku_list[(selected_idx + 2) % len(sku_list)]
]

worklist_data = []
for i, sku in enumerate(simulated_skus):
    vel = normal_velocity if i == 0 else sku_catalog[sku]["Calculated_Velocity"]
    
    exp_sales = vel * hours_zero_sales
    prob_zero = poisson.pmf(0, exp_sales)
    conf = (1 - prob_zero) * 100
    
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
st.dataframe(worklist_df, use_container_width=True, hide_index=True)
