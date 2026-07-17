## Inventory Intelligence Dashboard

**An early-warning system for "missing" inventory that 
may not actually be on the shelf.**

**Live demo:** https://inventory-intelligence-dashboard.streamlit.app/
**Dataset:** [UCI Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail)

---

**Critical:** Product flagged after 6 hours of no sales.

![Critical alert](assets/screenshots/Critical.png)

**Warning:** Product flagged after 2 hours of no sales.

![Warning status](assets/screenshots/Warning.png)

**Normal:** Even after 3 hours of no sales, this product's 
status is normal. When the sales gap falls within expected 
variance, the system raises no alert — avoiding unnecessary 
staff intervention.

![Normal status](assets/screenshots/Normal.png)

---

## The Phantom Inventory Problem

A retail store's inventory system may record an item as 
available, even though it is physically absent in the store 
or warehouse due to theft, misplacement, or damage. This 
situation is called the 'Phantom Inventory Problem,' and 
this dashboard addresses it.

This dashboard uses the historical sales frequency for each 
item, compares it to the period with no sales for that item, 
and flags the item for physical inspection if that period is 
abnormal, prioritising it for a physical shelf check.

This decreases invisible revenue leaks by allowing staff to 
prioritise inventory checks and correct inventory data errors.

---

## Repo Structure

```text
Inventory-Intelligence-Dashboard/
│
├── app.py                         # Streamlit dashboard — entry point
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
│
├── data/
│   ├── raw/                       # Place Online Retail.xlsx here
│   └── aggregated_catalog.csv     # Pre-processed output read by the dashboard
│
├── src/
│   └── data_preparation.py        # Full data pipeline from raw Excel to catalogue CSV
│
└── assets/
    └── screenshots/
        ├── Critical.png
        ├── Warning.png
        └── Normal.png
```

---

## How the Model Works

The dashboard asks one question: what is the statistical 
probability that a product with this historical sales rate 
will have zero sales over this given period — likely, or 
due to an inventory problem that needs investigation?

To answer it, the model calculates Lambda (λ) — simply the 
number of sales expected in a given time frame, all things 
being equal. Sales Velocity is how many units a product 
historically sells per hour.

**λ = Sales Velocity × Hours**

The output is the probability of zero sales. The dashboard 
converts this into an anomaly confidence score, which flips 
the probability for better understanding. For example, if 
the model says there is a 5% chance that the period of no 
sales is normal, the anomaly confidence says there is a 95% 
chance that this product needs to be investigated. The result 
is a colour-coded verdict — Normal, Warning, or Critical — 
so staff can act on it without needing to understand the 
statistics behind it.

---

## Key Decisions Made

1. **UK filter:** Filtered and used only the transactions from
the United Kingdom in the main dataset. This is a repurposed
dataset, and the United Kingdom location serves as one branch of a 
fictional retail store chain. Without this filter, the 
single-branch simulation breaks down.

2. **14-hour trading window:** I extracted the hours from 
the invoice date and discovered that transactions peaked at 
midday with 70,938 transactions and dropped to negligible 
volume by 20:00 — confirming a 14-hour window rather than 
assuming one. Without this, the model factors in 10 hours 
of no transactions and falls flat.

3. **Curated default catalogue:** Curated 6 items with 
varying velocities to display by default, selected from the 
dataset to show varying product behaviours. Without this, 
users would have to scroll through all 3,645 products.

4. **Velocity floor of 0.2:** Some products have very small 
velocities and will not flag realistically without a floor. 
At 0.2, a product takes 9 hours to trigger a Warning and 15 
hours to reach Critical at 95% sensitivity — still within a 
single working shift. Without this, slow-moving products 
would require weeks before being flagged for inspection.

---

## Real-World Limitations

1. The dataset was chosen deliberately and repurposed to 
simulate a branch of a physical retail store. This was done 
to showcase creative storytelling with data, rather than 
defaulting to a purpose-built demo dataset.

2. Does not account for false positives yet — there is no 
feedback loop to register real staff check outcomes. This 
would require staff to log the results of flagged items in 
a real deployment.

3. The 14-hour sales window does not account for time of 
day. There is no distinction between products that sell more 
at a particular time and those that sell less.

4. Does not account for burstiness, where a promotion or 
viral moment drastically changes the sales velocity for a 
short period.

---

## Tech Stack

Python · Streamlit · Pandas · NumPy · SciPy (Poisson)

---

## From Proof of Concept to Production

This dashboard was built as a proof of concept using a 
static historical dataset. A production version would need 
live point-of-sale data feeding directly into the model, so 
alerts reflect what is actually happening on the shelf right 
now rather than what historically should be happening.

It would also need to account for discounts, promotions, and 
seasonality — a product selling three times its normal rate 
during a promotion should not trigger a phantom inventory 
alert.

Finally, a staff feedback loop would allow the system to 
learn from real check outcomes over time, gradually reducing 
false positives and improving the confidence of each alert.
