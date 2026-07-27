"""
Inventory Intelligence Dashboard
---------------------------------
A retail store's inventory system may say an item is in stock when it
physically isn't, stolen, misplaced, or damaged. This is phantom inventory.

This tool uses a Poisson model to work out how unusual a sales gap is for
a given product, and only flags the ones worth a staff member checking.

The dataset is a UK-filtered subset of a public online retail dataset,
deliberately repurposed to simulate a single physical branch.
"""

import hashlib
import streamlit as st
import pandas as pd
from model import compute_anomaly_confidence

st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

DATA_FILE = "data/aggregated_catalog.csv"


@st.cache_data  # stops the CSV being re-read on every widget interaction
def load_catalog(filepath: str) -> dict:
    """Load product catalogue (SKU to description and sales velocity) from CSV."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(
            f"Data file '{filepath}' was not found. The app needs this "
            "file to run - please check it has been uploaded alongside "
            "the app script."
        )
        return {}
    except pd.errors.EmptyDataError:
        st.error(f"Data file '{filepath}' is empty. Nothing to display.")
        return {}

    if df.empty or "StockCode" not in df.columns:
        st.error(
            "Data file was loaded but is missing expected columns "
            "(StockCode). Please check the file was generated correctly."
        )
        return {}

    # StockCode as string to avoid silently dropping leading zeros (e.g. "07001" becomes 7001)
    df["StockCode"] = df["StockCode"].astype(str)
    catalog_df = df.set_index("StockCode")

    # Dict over DataFrame, the app only ever needs one SKU at a time, O(1) lookup
    return catalog_df.to_dict("index")


# Mock data only, not connected to any real warehouse, till, or pricing system

def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent fake shelf reference for a given SKU."""
    # md5 hash not random, same SKU must always map to the same location across reruns
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


def get_mock_unit_price(sku: str) -> float:
    """Generate a plausible but entirely fake unit price."""
    sku_digits = "".join(filter(str.isdigit, str(sku)))
    if not sku_digits:
        return 4.50
    return float((int(sku_digits) % 135 + 15) / 10)


full_catalog = load_catalog(DATA_FILE)
if not full_catalog:
    st.stop()  # error already shown in load_catalog()

# 6 SKUs selected to show a clear example from each alert tier at default
# settings (3 hours, 95% sensitivity): two Normal, two Warning, two Critical,
# so a first-time visitor sees the full range of outcomes without scrolling
# through all 3,645 products. Values are pulled live from the catalog below,
# never hardcoded, so they can't drift out of sync if the pipeline is rerun
# with updated data or logic.
CURATED_SKU_IDS = ["20663", "23077", "23313", "22999", "90214M", "22457"]
CURATED_SKUS = {
    sku: full_catalog[sku]
    for sku in CURATED_SKU_IDS
    if sku in full_catalog
}

st.sidebar.header("Simulation Controls")

show_all = st.sidebar.checkbox("View all Products")
sku_catalog = full_catalog if show_all else CURATED_SKUS

selected_sku = st.sidebar.selectbox(
    "Select Target Product",
    options=list(sku_catalog.keys()),
    index=min(4, len(sku_catalog) - 1),  # guards against short list going out of bounds
    format_func=lambda x: f"{sku_catalog[x]['Description']} ({x})",
)

default_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")

# key tied to selected_sku so switching products doesn't carry over stale slider values
normal_velocity = st.sidebar.slider(
    "Normal Sales Velocity (Units/Hour)",
    min_value=0.1,
    max_value=max(20.0, float(default_velocity) * 1.5),
    value=float(default_velocity),
    step=0.1,
    key=f"vel_{selected_sku}",
    help="How fast this product normally sells. Higher = a faster-moving product.",
)

hours_zero_sales = st.sidebar.slider(
    "Current Hours with Zero Sales",
    min_value=1,
    max_value=24,
    value=3,
    step=1,
    key=f"hrs_{selected_sku}",
    help="How many hours it's been since this product last sold. Drag this up to simulate a longer period.",
)

confidence_threshold = st.sidebar.slider(
    "Alert Sensitivity (%)",
    min_value=80,
    max_value=99,
    value=95,
    step=1,
    key="sensitivity_slider",
    help="How sure the model needs to be before it raises a CRITICAL alert. Lower = more alerts, higher = fewer but more certain ones.",
)

result = compute_anomaly_confidence(normal_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
phantom_stock_confidence = result["anomaly_confidence"]

# Warning fires 15 points below Critical, a watch tier before action is required
is_flagged = phantom_stock_confidence >= (confidence_threshold - 15)
is_critical = phantom_stock_confidence >= confidence_threshold

mock_price = get_mock_unit_price(selected_sku)
# Revenue only shown when item is flagged, a normal item gets no revenue figure at all
simulated_lost_revenue = expected_sales_in_window * mock_price if is_flagged else 0.0

st.title("Inventory Intelligence Dashboard")
st.markdown(
    "This is an intelligent inventory monitoring tool that identifies products with unusual"
    " low sales volume and prioritises them for investigation."
)

if is_critical:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has not sold in **{hours_zero_sales} hours**. "
        f"Based on its usual sales pattern, this is longer than expected and may indicate a stock issue. "
        f"A quick shelf check is recommended."
    )
elif is_flagged:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has not sold in the last **{hours_zero_sales} hours**, "
        f"despite usually selling around {normal_velocity:.0f} unit{'s' if normal_velocity >= 1.5 or normal_velocity < 0.5 else ''} per hour. "
        f"At this sales rate, we would normally expect some activity by now. Consider checking the shelf availability or inventory records."
    )
else:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has had no sales in the last **{hours_zero_sales} hours**. "
        f"This is not unusual because the product typically sells slowly, so a short period without sales is expected. "
        f"No action is recommended at this time."
    )

st.info(narrative_text)

with st.expander("How does the model decide what's suspicious?"):
    st.markdown("""
The model asks a simple question: based on how fast this product normally sells,
how likely is it to genuinely have zero sales this long?

Very unlikely, flags as suspicious.

Quite likely, no action required.

That probability is converted into a single anomaly confidence percentage for proper understanding.

**Important distinction:** this score measures how statistically unusual the period of zero sales is,
not the probability that stock is physically missing.
A high score means "this is worth checking," not "this is confirmed missing."

**Try it:** use the sliders in the sidebar to change the sales rate, hours without sales, or
confidence score, and watch the assessment below update in real time.
    """)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Normal Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Hours Since Last Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sales in This Window", f"{expected_sales_in_window:.1f} units")

st.markdown("---")
st.markdown("### Anomaly Assessment")

if is_critical:
    st.error(f"""
### CRITICAL: HIGH SHELF-CHECK PRIORITY ({phantom_stock_confidence:.1f}% Anomaly Score)
**What this means:** it is statistically unusual for this product to have no sales this long, 
 given its normal sales rate. This suggests it is worth physically checking the item at its 
  location immediately, it does not confirm stock is missing.
""")
elif is_flagged:
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Anomaly Score)
    **Observation:** Sales are unusually slow but still within marginal statistical variance. 
     Worth monitoring before physically checking the item at its location.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Score)
    **Observation:** This sales gap falls within expected normal variance. No action required.
    """)

if is_flagged:
    st.markdown("---")
    st.markdown("### Recommended Action")
    st.caption(
        "Shelf location and revenue figures below are simulated for "
        "demonstration purposes and are not connected to a real warehouse, "
        "till, or pricing system."
    )

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        st.metric("Where to Check", get_mock_shelf_location(selected_sku))
    with action_col2:
        st.metric("Potential Lost Revenue", f"£{simulated_lost_revenue:.2f}")

st.markdown("---")
st.markdown("### Floor Staff Worklist")
st.caption(
    "This table shows how flagged products could feed directly into a "
    "prioritised task list for staff, alongside the selected item's two "
    "neighbours in the catalogue for comparison. Shelf locations are "
    "simulated, not connected to a real warehouse system."
)

sku_list = list(sku_catalog.keys())
selected_idx = sku_list.index(selected_sku)

# The selected item uses the slider-adjusted velocity so the table reacts
# to the sliders above; its two neighbours use their real catalogue
# velocity, giving a mix of live-adjusted and real data in the same table.
worklist_skus = [
    selected_sku,
    sku_list[(selected_idx + 1) % len(sku_list)],
    sku_list[(selected_idx + 2) % len(sku_list)],
]

worklist_rows = []
for i, sku in enumerate(worklist_skus):
    velocity = normal_velocity if i == 0 else sku_catalog[sku]["Calculated_Velocity"]
    row_result = compute_anomaly_confidence(velocity, hours_zero_sales)
    row_confidence = row_result["anomaly_confidence"]

    if row_confidence >= confidence_threshold:
        tier = "CRITICAL"
    elif row_confidence >= (confidence_threshold - 15):
        tier = "WARNING"
    else:
        tier = "MONITOR"

    worklist_rows.append({
        "Task ID": f"TSK-{9400 + selected_idx + i}",
        "SKU": sku,
        "Description": sku_catalog[sku]["Description"],
        "Shelf Location": get_mock_shelf_location(sku),
        "Anomaly Score": f"{row_confidence:.1f}%",
        "Priority Tier": tier,
    })

worklist_df = pd.DataFrame(worklist_rows)
st.dataframe(worklist_df, use_container_width=True, hide_index=True)

st.markdown("---")
