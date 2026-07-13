"""
Inventory Intelligence Dashboard
---------------------------------
WHAT THIS APP DOES:
A store's till system knows exactly what SHOULD be selling. If a normally
fast-moving product suddenly stops selling for several hours, that's often
a sign it's not actually on the shelf anymore (misplaced, damaged, stolen,
or a listing error) - even though the computer still says it's in stock.
This is called "phantom inventory".

Rather than making a staff member manually check every slow product, this
tool uses a statistical model (Poisson distribution) to work out how
UNUSUAL a sales gap really is for that specific product, and only flags
the ones worth a human going to check.

NOTE ON DATA: the underlying dataset is a UK-filtered subset of a public
online retail dataset, deliberately repurposed here to simulate a single
physical branch. See README for full details on this design choice.
"""

import streamlit as st
import pandas as pd
from scipy.stats import poisson
import hashlib

st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

# =============================================================================
# SECTION 1: LOADING THE DATA
# =============================================================================
DATA_FILE = "aggregated_catalog.csv"


@st.cache_data  # avoids re-reading the CSV from disk on every widget interaction
def load_catalog(filepath: str) -> dict:
    """
    Load the pre-calculated product catalogue (SKU -> description + normal
    sales velocity) from a CSV file.
    """
    # Fail loudly but gracefully - a missing/empty file should stop the app
    # with a clear message, not crash further down with a confusing traceback.
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

    # Force StockCode to string - as a number it would silently drop
    # leading zeros (e.g. "07001" -> 7001), corrupting the SKU.
    df["StockCode"] = df["StockCode"].astype(str)
    catalog_df = df.set_index("StockCode")

    # Dict, not DataFrame: the rest of the app only ever needs "give me
    # this one SKU's data", so a dict gives O(1) lookup by key.
    return catalog_df.to_dict("index")


# Hardcoded rather than loaded from file - a fixed, curated demo set so a
# first-time visitor sees a manageable view instead of the full catalogue.
CURATED_SKUS = {
    "22439": {"Description": "6 ROCKET BALLON", "Calculated_Velocity": 0.59},
    "22046": {"Description": "TEA WRAPPING PAPER", "Calculated_Velocity": 0.59},
    "22713": {"Description": "CARD I LOVE LONDON", "Calculated_Velocity": 1.13},
    "17003": {"Description": "BROCADE RING PURSE", "Calculated_Velocity": 8.04},
    "90062": {"Description": "CARNIVAL BRACELET", "Calculated_Velocity": 0.20},
    "22670": {"Description": "FRENCH WC SIGN BLUE METAL", "Calculated_Velocity": 0.53},
}


# =============================================================================
# SECTION 2: THE STATISTICAL MODEL
# =============================================================================
def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> dict:
    """
    Work out how UNUSUAL it is that a product has had zero sales for a
    given number of hours, given how fast it normally sells.

    Kept as a pure function (no Streamlit calls, no side effects) so the
    logic can be unit-tested or reused outside this dashboard.
    """
    expected_sales = velocity * hours_since_last_sale  # this is "lambda" for the Poisson model

    # scipy over hand-rolled maths: this is a well-established, peer-reviewed
    # implementation, not something worth reinventing.
    probability_of_zero_sales = poisson.pmf(0, expected_sales)

    # Flip probability of an innocent zero into a "confidence something's
    # wrong" score - easier for a non-technical user to act on.
    anomaly_confidence = (1 - probability_of_zero_sales) * 100

    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_confidence": anomaly_confidence,
    }


# =============================================================================
# SECTION 3: SIMULATED OPERATIONAL DETAILS (MOCK DATA)
# =============================================================================
# Everything below is FAKE data for demo purposes only - not read from any
# real warehouse, till, or pricing system. Also disclosed in the UI itself.

def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent, fake aisle/shelf reference for a given SKU."""
    # md5 hash instead of random: same SKU must always map to the same fake
    # location, or it'd look like the product moves shelves every rerun.
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


def get_mock_unit_price(sku: str) -> float:
    """Generate a plausible-looking but entirely FAKE unit price."""
    sku_digits = "".join(filter(str.isdigit, str(sku)))
    if not sku_digits:
        return 4.50
    return float((int(sku_digits) % 135 + 15) / 10)


# =============================================================================
# SECTION 4: APP LAYOUT & CONTROL FLOW
# =============================================================================
# Streamlit reruns this whole script on every interaction - @st.cache_data
# above is what stops that from meaning "reload the CSV every time".

full_catalog = load_catalog(DATA_FILE)
if not full_catalog:
    st.stop()  # error already shown inside load_catalog(); stop before anything else can crash

st.sidebar.header("Simulation Controls")

show_all = st.sidebar.checkbox("View all Products")
sku_catalog = full_catalog if show_all else CURATED_SKUS

selected_sku = st.sidebar.selectbox(
    "Select Target Product",
    options=list(sku_catalog.keys()),
    index=min(4, len(sku_catalog) - 1),  # min() guards against a short list going out of bounds
    format_func=lambda x: f"{sku_catalog[x]['Description']} ({x})",
)

default_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")

# key=f"..._{selected_sku}" ties each slider's remembered position to the
# selected product, so switching products doesn't carry over a stale value.
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
    help="How many hours it's been since this product last sold. Drag this up to simulate a longer silence.",
)

confidence_threshold = st.sidebar.slider(
    "Confidence Score (%)",
    min_value=80,
    max_value=99,
    value=95,
    step=1,
    key="sensitivity_slider",
    help="How sure the model needs to be before it raises a CRITICAL alert. Lower = more alerts, higher = fewer but more certain ones.",
)

# Calculated once, reused everywhere below - keeps every section of the
# page consistent with a single source of truth.
result = compute_anomaly_confidence(normal_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
phantom_stock_confidence = result["anomaly_confidence"]

# Two-tier flagging: is_flagged (watch) is a softer threshold than
# is_critical (act now), both driven off the user's own sensitivity slider.
is_flagged = phantom_stock_confidence >= (confidence_threshold - 15)
is_critical = phantom_stock_confidence >= confidence_threshold

mock_price = get_mock_unit_price(selected_sku)
# No revenue figure at all for a normal item - not even zero - so the page
# never implies a risk that isn't actually being flagged.
simulated_lost_revenue = expected_sales_in_window * mock_price if is_flagged else 0.0

# --- UI Header ---
st.title("Inventory Intelligence Dashboard")
st.markdown(
    "An intelligent inventory monitoring tool that identifies products with unusual"
    " sales inactivity and prioritises them for investigation."
)

# --- Plain-language narrative, translating the stats into a decision ---
if is_critical:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has been inactive for **{hours_zero_sales} hours**. "
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
The model asks a simple question: based on how fast this product normally sells, how likely is it to genuinely have zero sales this long?

Very unlikely → flags as suspicious.

Quite likely → no action required.

That likelihood is converted into a single confidence score (e.g. "97% confidence something's wrong"), so staff can act on it without needing to understand the statistics.

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
    ### CRITICAL: PHANTOM INVENTORY SUSPECTED ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** Verify the item at its location immediately.
    """)
elif is_flagged:
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** Sales are unusually slow but still within marginal statistical variance. Worth monitoring before dispatching staff.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** This sales gap falls within expected normal variance. No action required.
    """)

# Only renders for flagged items - a normal item gets no action card,
# rather than a card with placeholder/zeroed-out values.
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
