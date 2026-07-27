## Inventory Intelligence Dashboard

**A proof-of-concept decision-support dashboard that uses statistical anomaly detection to prioritise products for physical shelf checks.**

**Live demo:** https://inventory-intelligence-dashboard.streamlit.app/
**Dataset:** [UCI Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail)

This project shows how historical sales patterns can be used to identify which products should be prioritised for a physical shelf check. It does not confirm inventory discrepancies on its own as doing that would require live data from point-of-sale systems, warehouse records, and shelf-availability tools, which is outside the scope of this project.

---

**Critical:** A high-velocity product reaches Critical after six hours without a sale.

![Critical alert](assets/screenshots/Critical.png)

**Warning:** Product flagged after 2 hours of no sales.

![Warning status](assets/screenshots/Warning.png)

**Normal:** For this slower-moving product, three hours without a sale remains within 
its expected pattern.

![Normal status](assets/screenshots/Normal.png)

---

## The problem

A retail store's inventory system may record an item as available even though it is physically absent, due to theft, misplacement, or damage. Walking the floor to manually check every slow-moving item consumes time and may be difficult to prioritise, but ignoring the problem means nothing may be done. This dashboard flags the products statistically worth a physical checking.

## Business objective

Demonstrate how past transaction behavior can be turned into some straightforward decision support, to help prioritize the physical inventory checks.

## How it works

The dashboard compares each product's historical sales rate to how long it's actually been since its last sale, and calculates how statistically unusual that gap is using a Poisson model. A high score means "worth checking," not "confirmed missing." Full methodology, including synthetic model behaviour checks, is in [docs/methodology.md](docs/methodology.md).

## Key assumptions and design decisions

- **UK-filtered subset**, treated as a stand-in for a single store branch
- **14-hour trading window**, informed by the hourly distribution of UK transactions.
- **Six curated example products**, spanning Normal, Warning, and Critical at default settings
- **A monitoring velocity floor**, kept separate from the true observed velocity for transparency

Full reasoning behind each decision is in [docs/methodology.md](docs/methodology.md).

## Limitations

Built on historical averages, not live conditions. No ground-truth validation yet, no feedback loop to confirm real outcomes. Doesn't yet account for seasonality, promotions, or bursty demand. See the full limitations and implications: [docs/limitations.md](docs/limitations.md).

## Business Analytics skills demonstrated
- **Problem Definition**

## Tech stack

Python · Streamlit · Pandas · NumPy · SciPy (Poisson)

## Read more

- [Business case](docs/business-case.md), estimated impact and next steps toward production
- [Methodology](docs/methodology.md), the Poisson maths, model validation results, and the trading-hours derivation
- [Limitations](docs/limitations.md), full limitations list and why they're stated explicitly

