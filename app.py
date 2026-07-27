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


@st.cache_data
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

    df["StockCode"] = df["StockCode"].astype(str)
    catalog_df = df.set_index("StockCode")
    return catalog_df.to_dict("index")


def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent fake shelf reference for a given SKU."""
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


def get_mock_unit_price(sku: str) -> float:
    """Generate a plausible but entirely fake unit price."""
    sku_digits = "".join(filter(str.isdigit, str(sku)))
    if not sku_digits:
        return 4.50
    return float((int(sku_digits) % 135 + 15) / 10)


def classify(score: float, threshold: float) -> str:
    """
    Shared classification logic so the single-product view and the
    worklist always use the same three-tier vocabulary: Normal, Warning,
    Critical. Warning begins 15 points below the Critical threshold,
    a demonstration business rule, see BR01 in docs/requirements.md,
    not an empirically validated one.
    """
    if score >= threshold:
        return "Critical"
    elif score >= (threshold - 15):
        return "Warning"
    else:
        return "Normal"


full_catalog = load_catalog(DATA_FILE)
if not full_catalog:
    st.stop()

# 6 SKUs selected to show a clear example from each alert tier at default
# settings (3 hours, 95% threshold): two Normal, two Warning, two Critical,
# so a first-time visitor sees the full range of outcomes without scrolling
# through all products. Values are pulled live from the catalog below,
# never hardcoded, so they can't drift out of sync if the pipeline is rerun
# with updated data or logic.
CURATED_SKU_IDS = ["20663", "90214M", "23313", "22999", "23077", "22457"]
CURATED_SKUS = {
    sku: full_catalog[sku]
    for sku in CURATED_SKU_IDS
    if sku in full_catalog
}

st.sidebar.header("Scenario Inputs")

show_all = st.sidebar.checkbox("View all Products")
sku_catalog = full_catalog if show_all else CURATED_SKUS

selected_sku = st.sidebar.selectbox(
    "Select Target Product",
    options=list(sku_catalog.keys()),
    index=min(4, len(sku_catalog) - 1),
    format_func=lambda x: f"{sku_catalog[x]['Description']} ({x})",
)

observed_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")

# Labelled as "assumed" rather than "normal" because this is a scenario
# input the user controls, not a live read of the product's actual
# historical rate. The real observed rate is shown separately below.
assumed_velocity = st.sidebar.slider(
    "Assumed Sales Velocity (Units/Hour)",
    min_value=0.1,
    max_value=max(20.0, float(observed_velocity) * 1.5),
    value=float(observed_velocity),
    step=0.1,
    key=f"vel_{selected_sku}",
    help="The sales rate used for this scenario. Defaults to the product's observed historical rate, shown below, but can be adjusted to explore other scenarios.",
)

if abs(assumed_velocity - observed_velocity) > 0.01:
    st.sidebar.caption(f"Observed historical rate for this product: {observed_velocity:.2f} units/hr")

hours_zero_sales = st.sidebar.slider(
    "Current Hours with Zero Sales",
    min_value=1,
    max_value=24,
    value=3,
    step=1,
    key=f"hrs_{selected_sku}",
    help="How many hours it's been since this product last sold. Drag this up to simulate a longer period.",
)

critical_threshold = st.sidebar.slider(
    "Critical Alert Threshold (%)",
    min_value=80,
    max_value=99,
    value=95,
    step=1,
    key="threshold_slider",
    help="Products with anomaly scores at or above this threshold are classified as Critical. Lower thresholds generate more alerts, sooner, at the cost of more false alarms.",
)

result = compute_anomaly_confidence(assumed_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
anomaly_score = result["anomaly_confidence"]

status = classify(anomaly_score, critical_threshold)
is_flagged = status in ("Warning", "Critical")
is_critical = status == "Critical"

mock_price = get_mock_unit_price(selected_sku)
simulated_revenue_exposure = expected_sales_in_window * mock_price if is_flagged else 0.0

st.title("Inventory Intelligence Dashboard")
st.markdown(
    "This dashboard identifies products with unusual periods of no sales "
    "and prioritises them for a physical check."
)

if is_critical:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has not sold in **{hours_zero_sales} hours**. "
        f"Based on its usual sales pattern, this is longer than expected and may indicate a stock issue. "
        f"A shelf check is recommended as high priority."
    )
elif status == "Warning":
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has not sold in the last **{hours_zero_sales} hours**, "
        f"despite usually selling around {assumed_velocity:.0f} unit{'s' if assumed_velocity >= 1.5 or assumed_velocity < 0.5 else ''} per hour. "
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

That probability is converted into a single anomaly score for easier interpretation.

**Important distinction:** this score measures how statistically unusual the period of zero sales is,
not the probability that stock is physically missing.
A high score means "this is worth checking," not "this is confirmed missing."

**Try it:** use the sliders in the sidebar to change the sales rate, hours without sales, or
the critical threshold, and watch the assessment below update in real time.
    """)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Assumed Sales Rate", f"{assumed_velocity:.2f} units/hr")
with col2:
    st.metric("Hours Since Last Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sales in This Window", f"{expected_sales_in_window:.1f} units")

st.markdown("---")
st.markdown("### Anomaly Assessment")

if is_critical:
    st.error(f"""
### CRITICAL: HIGH SHELF-CHECK PRIORITY ({anomaly_score:.1f}% Anomaly Score)
**What this means:** it is statistically unusual for this product to have zero sales this long, given its assumed rate. This flags it as worth a physical check, it does not confirm stock is missing.
**Recommended action:** treat this as a high-priority item to verify at its location.
""")
elif status == "Warning":
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({anomaly_score:.1f}% Anomaly Score)
    **Observation:** Sales are unusually slow but still within the expected range for this threshold. Worth monitoring before dispatching staff.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({anomaly_score:.1f}% Anomaly Score)
    **Observation:** This sales gap falls within expected variance for this product. No action required.
    """)

if is_flagged:
    st.markdown("---")
    st.markdown("### Recommended Action")
    st.caption(
        "Shelf location and revenue figures below are simulated for "
        "demonstration purposes and are not connected to a real warehouse, "
        "till, or pricing system. The revenue figure is illustrative exposure, "
        "not a confirmed loss."
    )

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        st.metric("Where to Check", get_mock_shelf_location(selected_sku))
    with action_col2:
        st.metric("Illustrative Revenue Exposure", f"£{simulated_revenue_exposure:.2f}")

st.markdown("---")
st.markdown("### Priority Worklist")
st.caption(
    "The five products with the highest anomaly score across the whole "
    "catalogue, for the same hours-without-sale scenario set above, using "
    "each product's own observed velocity, not the assumed rate above. "
    "This is a genuinely ranked list, not neighbouring catalogue entries. "
    "Shelf locations are simulated, not connected to a real warehouse system."
)

worklist_rows = []
for sku, details in full_catalog.items():
    row_score = compute_anomaly_confidence(details["Calculated_Velocity"], hours_zero_sales)["anomaly_confidence"]
    worklist_rows.append({
        "SKU": sku,
        "Description": details["Description"],
        "Shelf Location": get_mock_shelf_location(sku),
        "Anomaly Score": row_score,
        "Status": classify(row_score, critical_threshold),
    })

worklist_df = (
    pd.DataFrame(worklist_rows)
    .sort_values("Anomaly Score", ascending=False)
    .head(5)
    .reset_index(drop=True)
)
worklist_df.insert(0, "Task ID", [f"TSK-{9400 + i}" for i in range(len(worklist_df))])
worklist_df["Anomaly Score"] = worklist_df["Anomaly Score"].map(lambda x: f"{x:.1f}%")

st.dataframe(worklist_df, use_container_width=True, hide_index=True)

st.markdown("---")
