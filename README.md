## Inventory Intelligence Dashboard

**An early-warning system for "missing" inventory that may not actually be on the shelf.**

**Live demo:** https://inventory-intelligence-dashboard.streamlit.app/
**Dataset:** [UCI Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail)

**Critical:** Product flagged after 6 hours of no sales.

![Critical alert](assets/screenshots/Critical.png)

**Warning:** Product flagged after 2 hours of no sale

![Warning status](assets/screenshots/Warning.png)

**Normal:** Even after 3 hours of no sale, this product's staus is normal.
When the sales gap falls within expected variance, the system raises no alert, avoiding unnecessary staff intervention.

![Normal status](assets/screenshots/Normal.png)


---

## The Phantom Inventory Problem

A retail store’s inventory system may record an item as available, even though it is physically absent in the store or warehouse due to theft, misplacement or damage. This situation is called the ‘Phantom Inventory Problem,’ and this dashboard addresses it.
This dashboard uses the historical sales frequency for each Item, compares it to the period with no sales for that Item, and flags the Item for physical inspection if that period is abnormal, prioritising the Item for a physical shelf location check.
This decreases invisible revenue leaks by allowing staff to prioritize inventory checks and correct inventory data errors.

---

## Repo Structure

Inventory-Intelligence-Dashboard/
│
├── app.py                          # Main Pipeline
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
│
├── data/
│   ├── raw/                        
│   └── aggregated_catalog.csv     
│
├── src/
│   └── data_preparation.py         
│
└── assets/
    └── screenshots/
        ├── Critical.png
        ├── Warning.png
        └── Normal.png



---

## How the Model Works

The dashboard asks the question: What is the statistical probability that a product with this historical sales rate will have zero sales over this given period? It uses Lambda (λ), which is simply the number of sales expected at this time frame, all things being equal.
                              λ= Sales Velocity × Hours
Sales Velocity is simply how many units a product historically sells per hour.

The output of the model is the probability of zero sales. The dashboard shows the anomaly confidence, which flips the probability output for better understanding. For example, the model says there is a 5% chance that the period of no sales is normal; the anomaly confidence says there's a 95% chance that this product needs to be investigated.

---

## Key Decisions made 

1. Filtered and used only the United Kingdom location in the main dataset. This is a repurposed dataset, and the United Kingdom location is to serve as one branch of a fictional retail store chain. Without it, the narrative of a store location will be defeated. 
2. Restricted the model to a 14-hour window. I extracted the hours from the invoice date and discovered that transactions peaked at midday, with 70,938 transactions, and dropped to negligible volume by 20:00, confirming a 14-hour window rather than assuming one. Without this, the model factors in the 10 hours of no transactions and falls flat.
3. Curated 6 items with varying velocities to display by default. This was done using their velocities from the dataset to show varying product behaviours by default. Without this, users will have to scroll through the whole dataset, which contains 3,645 products.
4. Set floor velocity to 0.2. This is because some products have small velocities and will not flag realistically. At the 0.2 floor, a product takes 9 hours to trigger a Warning and 15 hours to reach Critical at 95% sensitivity — still within a single working day shift. Without this, slow-moving products will require weeks before being flagged for inspection. 


---

## Real-world Limitations 

1. The dataset was chosen deliberately and repurposed to simulate a branch of a physical retail store. This was done to showcase creative storytelling with data, rather than defaulting to a purpose-built demo dataset.
2. Does not account for false positives yet because there is no feedback loop to register the real staff check outcomes. This will require staff to log outcomes of flagged items in real deployment. 
3. The 14-hour sales window that was extracted from the dataset does not account for the time of day. There is no distinction between products that sell more at a particular time and those that sell less.
4. Does not account for burstiness, where a promotion or viral moment drastically changes the sales velocity for a short period.


---

## Tech Stack: Python · Streamlit · Pandas · NumPy · SciPy (Poisson)

---
## From Proof of Concept to Production

This dashboard was built as a proof of concept using a static historical dataset. A production version would need live point-of-sale data feeding directly into the model, so alerts reflect what is actually happening on the shelf right now rather than what historically should be happening.
It would also need to account for discounts, promotions and seasonality, a product selling three times its normal rate during a promotion should not trigger a phantom inventory alert. 
Finally, a staff feedback loop would allow the system to learn from real check outcomes over time, gradually reducing false positives and improving the confidence of each alert.
