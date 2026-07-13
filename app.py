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

# ---------------------------------------------------------------------------
# IMPORTS: bringing in external code libraries this app depends on.
#   - streamlit: builds the interactive web dashboard (buttons, sliders, etc.)
#   - pandas: reads and manipulates tabular data (like an Excel sheet in code)
#   - scipy.stats.poisson: the specific statistical formula used for the
#     "how unusual is this?" calculation
#   - hashlib: a standard Python library for turning text into a scrambled,
#     consistent code — used here just to generate a fake but repeatable
#     shelf location, not for anything security-related
# ---------------------------------------------------------------------------
import streamlit as st
import pandas as pd
import scipy.stats as stats
from scipy.stats import poisson
import hashlib

# Configures the browser tab title and makes the page use the full screen
# width rather than a narrow centred column.
st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

# =============================================================================
# SECTION 1: LOADING THE DATA
# =============================================================================
# Name of the input file this app reads from. Defined once as a constant
# (written in CAPITAL_LETTERS by Python convention) so if the filename ever
# changes, it only needs to be updated in this one place.
DATA_FILE = "aggregated_catalog.csv"


# The line above this function, "@st.cache_data", is a Python "decorator".
# It tells Streamlit: "run this function once, remember the result, and
# reuse it on future reruns instead of re-reading the file every time the
# user moves a slider." This keeps the app fast, since reloading a CSV file
# from disk on every single interaction would be slow and unnecessary.
@st.cache_data
def load_catalog(filepath: str) -> dict:
    """
    Load the pre-calculated product catalogue (SKU -> description + normal
    sales velocity) from a CSV file.
    """
    # "try/except" is Python's error-handling structure: attempt the code
    # inside "try", and if a specific, anticipated problem occurs, "except"
    # catches it and handles it gracefully instead of crashing the whole app.
    try:
        # Reads the CSV file into a pandas "DataFrame" — a table-like
        # structure with rows and columns, similar to a spreadsheet.
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        # This specific error happens if the file doesn't exist at that
        # location. Rather than showing a confusing technical crash, this
        # shows a clear, human-readable red error message in the app.
        st.error(
            f"Data file '{filepath}' was not found. The app needs this "
            "file to run - please check it has been uploaded alongside "
            "the app script."
        )
        # Returns an empty dictionary so the rest of the app knows loading
        # failed and can stop gracefully, rather than crashing further down.
        return {}
    except pd.errors.EmptyDataError:
        # This error happens if the file exists but has no data in it.
        st.error(f"Data file '{filepath}' is empty. Nothing to display.")
        return {}

    # A second safety check: even if the file loaded without an error, make
    # sure it actually contains the column this app depends on ("StockCode").
    # "df.empty" checks if the table has zero rows.
    if df.empty or "StockCode" not in df.columns:
        st.error(
            "Data file was loaded but is missing expected columns "
            "(StockCode). Please check the file was generated correctly."
        )
        return {}

    # Ensures every SKU code is treated as text (not a number), so codes
    # like "07001" don't accidentally lose their leading zero.
    df["StockCode"] = df["StockCode"].astype(str)

    # Makes "StockCode" the table's row label (its "index"), so each
    # product can be looked up directly by its SKU code.
    catalog_df = df.set_index("StockCode")

    # Converts the table into a Python "dictionary" — a structure that maps
    # a unique key (here, each SKU code) to a bundle of related information
    # (its description and sales velocity). Dictionaries are used throughout
    # this app because they allow instant lookup: "give me SKU 90062" returns
    # its details immediately, without having to search through a whole list.
    return catalog_df.to_dict("index")


# A small, hand-picked dictionary of six example products, used as the
# default view so a first-time visitor sees a manageable, illustrative set
# rather than being dropped into the full catalogue immediately. This is
# written directly in the code (rather than loaded from a file) because it's
# a fixed set of curated examples, not something that should change if the
# underlying data is refreshed.
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
# This function contains the core logic of the whole app: given how fast a
# product normally sells, and how many hours it's been silent, work out how
# suspicious that silence is.
#
# The "-> dict" at the end of the function's first line is a type hint: it
# tells any reader that this function will hand back a dictionary.
def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> dict:
    """
    Work out how UNUSUAL it is that a product has had zero sales for a
    given number of hours, given how fast it normally sells.
    """
    # Step 1: work out how many units we'd normally expect to have sold in
    # this time window, if nothing was wrong (normal pace × hours silent).
    # In statistical terms, this number is called "lambda" — the single
    # figure the Poisson distribution needs to make its calculation.
    expected_sales = velocity * hours_since_last_sale

    # Step 2: ask the Poisson distribution "what's the probability of
    # seeing exactly zero (0) sales, given that we expected this many?"
    # poisson.pmf(0, expected_sales) is a ready-made statistical formula
    # from the scipy library — this app doesn't calculate the maths by
    # hand, it calls a trusted, well-established function to do it.
    probability_of_zero_sales = poisson.pmf(0, expected_sales)

    # Step 3: flip that probability into a "confidence" percentage that
    # something IS wrong. If there was only a 3% chance of a genuine zero,
    # that becomes a 97% confidence the silence is suspicious.
    anomaly_confidence = (1 - probability_of_zero_sales) * 100

    # Bundles all three results into a dictionary so the calling code can
    # access each one by name (e.g. result["anomaly_confidence"]), which is
    # clearer to read than returning three separate unlabelled numbers.
    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_confidence": anomaly_confidence,
    }


# =============================================================================
# SECTION 3: SIMULATED OPERATIONAL DETAILS (MOCK DATA)
# =============================================================================
# IMPORTANT: everything in this section is FAKE data, generated purely to
# make the demo look and feel like a real operational tool. It is not read
# from any real warehouse system, till, or pricing database. This is stated
# clearly in the app's interface as well, not just here in the code.

def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent, fake aisle/shelf reference for a given SKU."""
    # hashlib.md5(...) scrambles the SKU code into a long, unique number.
    # The same SKU always produces the same scrambled number, which is what
    # makes this location "consistent" (SKU 90062 always maps to the same
    # fake aisle) without needing to store it anywhere.
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)

    # The "%" symbol is Python's "modulo" operator — it returns the
    # remainder after division. Used here purely to turn a huge scrambled
    # number into a small, realistic-looking aisle/shelf number and letter.
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


def get_mock_unit_price(sku: str) -> float:
    """Generate a plausible-looking but entirely FAKE unit price."""
    # "filter(str.isdigit, str(sku))" goes through every character in the
    # SKU code and keeps only the digits, discarding any letters.
    sku_digits = "".join(filter(str.isdigit, str(sku)))
    if not sku_digits:
        return 4.50
    return float((int(sku_digits) % 135 + 15) / 10)


# =============================================================================
# SECTION 4: APP LAYOUT & CONTROL FLOW
# =============================================================================
# From this point on, the code runs top-to-bottom every time the user
# interacts with the app (e.g. moves a slider) — this is how Streamlit apps
# work: the whole script re-runs, but @st.cache_data (used above) prevents
# the slow parts, like reloading the file, from repeating unnecessarily.

# Calls the function defined earlier and stores the resulting dictionary.
full_catalog = load_catalog(DATA_FILE)

# If loading failed, load_catalog() returned an empty dictionary, which
# Python treats as "False" in an if-check. st.stop() halts the app here so
# nothing below tries to run on missing data and crash with a confusing error.
if not full_catalog:
    st.stop()

st.sidebar.header("Simulation Controls")

# A checkbox that returns True or False depending on whether it's ticked.
show_all = st.sidebar.checkbox("View all Products")

# A one-line conditional (Python's "ternary" expression): if show_all is
# True, use the full catalogue; otherwise, use the small curated list.
sku_catalog = full_catalog if show_all else CURATED_SKUS

selected_sku = st.sidebar.selectbox(
    "Select Target Product",
    # "sku_catalog.keys()" returns every SKU code in the dictionary; wrapping
    # it in list() turns that into a plain list the dropdown can display.
    options=list(sku_catalog.keys()),
    index=min(4, len(sku_catalog) - 1),
    # "format_func" controls how each option is displayed on screen, without
    # changing the underlying value. A "lambda" is a small, throwaway
    # function written in a single line — here it just decides that each
    # dropdown entry should show the product's name followed by its SKU
    # code in brackets.
    format_func=lambda x: f"{sku_catalog[x]['Description']} ({x})",
)

# Looks up the chosen product's details in the dictionary using its SKU
# code as the key — the same lookup-by-key pattern used throughout this app.
default_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")  # A horizontal divider line in the sidebar.

# Sliders let the user manually set values to test different scenarios.
# "key=" gives each slider a unique internal identity so Streamlit doesn't
# confuse one slider's state with another's when the selected product changes.
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

# --- Run the statistical model once here, then reuse the result everywhere
# below. Calculating it once (rather than repeating the maths in multiple
# places) avoids duplicated logic and keeps every part of the page consistent.
result = compute_anomaly_confidence(normal_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
phantom_stock_confidence = result["anomaly_confidence"]

# Two True/False ("Boolean") flags that decide what the rest of the page
# shows. "is_flagged" covers both WARNING and CRITICAL; "is_critical" is
# the more serious subset of that.
is_flagged = phantom_stock_confidence >= (confidence_threshold - 15)
is_critical = phantom_stock_confidence >= confidence_threshold

mock_price = get_mock_unit_price(selected_sku)
# Only calculates a "potential lost revenue" figure if the item is actually
# flagged — an item behaving normally shouldn't display a revenue-risk
# number at all, since there's no risk being flagged in the first place.
simulated_lost_revenue = expected_sales_in_window * mock_price if is_flagged else 0.0

# --- UI Header ---
st.title("Inventory Intelligence Dashboard")
st.markdown(
    "An intelligent inventory monitoring tool that identifies products with unusual"
    " sales inactivity and prioritises them for investigation."
)

# --- Plain-language walkthrough, visible by default (not hidden in an expander) ---
# Dynamically generates the descriptive narrative depending on the critical threshold
# state instead of printing raw values and calculation fields.
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

# Render the dynamic plain-language narrative box
st.info(narrative_text)

# st.expander creates a collapsible section — closed by default, so it
# doesn't overwhelm the page, but still available to anyone who wants the
# fuller explanation of the statistical method behind the headline numbers.
with st.expander("How does the model decide what's suspicious?"):
    st.markdown("""
The model asks a simple question: based on how fast this product normally sells, how likely is it to genuinely have zero sales this long?

Very unlikely → flagged as suspicious, since a normal quiet spell wouldn't last this long.

Quite likely → left alone, since slow-sellers naturally have gaps.

That likelihood is converted into a single confidence score (e.g. "97% confidence something's wrong"), so staff can act on it without needing to understand the statistics.

**Try it:** use the sliders in the sidebar to change the sales rate, hours without sales, or
confidence score, and watch the assessment below update in real time.
    """)

st.markdown("---")

# --- Top-level metrics: three headline numbers shown as compact cards. ---
# st.columns(3) splits the page horizontally into three equal sections so
# the metrics sit neatly side by side instead of stacking vertically.
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Normal Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Hours Since Last Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sales in This Window", f"{expected_sales_in_window:.1f} units")

st.markdown("---")

# --- Anomaly Assessment: the main verdict, colour-coded for quick scanning ---
st.markdown("### Anomaly Assessment")

# An if / elif / else chain checks conditions in order and runs only the
# first block that matches — so an item can only ever be shown as ONE of
# CRITICAL, WARNING, or NORMAL, never more than one at once.
if is_critical:
    # st.error renders a red box - Streamlit's built-in visual style for
    # the most serious, attention-grabbing message.
    st.error(f"""
    ### CRITICAL: PHANTOM INVENTORY SUSPECTED ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** Verify the item at its location immediately.
    """)
elif is_flagged:
    # st.warning renders an amber/yellow box - a step down in urgency from
    # st.error, used for the "worth watching" middle tier.
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** Sales are unusually slow but still within marginal statistical variance. Worth monitoring before dispatching staff.
    """)
else:
    # st.success renders a green box - Streamlit's default style for a
    # positive, "all clear" outcome.
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** This sales gap falls within expected normal variance. No action required.
    """)

# --- Action card: this whole block only renders if is_flagged is True.
# A genuinely normal item shows no action card at all, rather than an
# empty or zeroed-out one, so the page doesn't imply there's something to
# act on when there isn't.
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
