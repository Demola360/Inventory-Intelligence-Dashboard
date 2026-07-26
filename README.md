## Inventory Intelligence Dashboard

**A proof-of-concept dashboard that flags products worth a physical shelf check, using statistical anomaly detection instead of manual floor walks.**

**Live demo:** https://inventory-intelligence-dashboard.streamlit.app/
**Dataset:** [UCI Online Retail Dataset](https://archive.ics.uci.edu/dataset/352/online+retail)

This project shows how historical sales patterns can be used to identify which products should be prioritised for a physical shelf check. It does not confirm inventory discrepancies on its own, doing that would require live data from point-of-sale systems, warehouse records, and shelf-availability tools, which is outside the scope of this project.

---

**Critical:** Product flagged after 6 hours of no sales.

![Critical alert](assets/screenshots/Critical.png)

**Warning:** Product flagged after 2 hours of no sales.

![Warning status](assets/screenshots/Warning.png)

**Normal:** Even after 3 hours of no sales, this product's status is normal.

![Normal status](assets/screenshots/Normal.png)

---

## The problem

A retail store's inventory system may record an item as available even though it's physically absent, due to theft, misplacement, or damage. Walking the floor to manually check every slow-moving item wastes staff time, but ignoring the problem means lost sales sitting on a shelf nobody can find. This dashboard flags the products statistically worth checking, instead of checking everything or nothing.

## How it works, in short

The dashboard compares each product's normal sales rate to how long it's actually been since its last sale, and calculates how statistically unusual that gap is using a Poisson model. A high score means "worth checking," not "confirmed missing." Full methodology, including the maths and the validation results, is in [docs/methodology.md](docs/methodology.md).

## Key decisions

- **UK-filtered subset**, treated as a stand-in for a single store branch
- **14-hour trading window**, derived empirically from the UK-only hourly transaction data, not assumed
- **Six curated example products**, spanning Normal, Warning, and Critical at default settings
- **A monitoring velocity floor**, kept separate from the true observed velocity for transparency

Full reasoning behind each decision is in [docs/methodology.md](docs/methodology.md).

## Limitations

Built on historical averages, not live conditions. No ground-truth validation yet, no feedback loop to confirm real outcomes. Doesn't yet account for seasonality, promotions, or bursty demand. Full limitations list and why they're included on purpose: [docs/limitations.md](docs/limitations.md).

## Tech stack

Python · Streamlit · Pandas · NumPy · SciPy (Poisson)

## Read more

- [Methodology](docs/methodology.md), the Poisson maths, model validation results, and the trading-hours derivation
- [Limitations](docs/limitations.md), full limitations list and why they're stated explicitly
- [Business case](docs/business-case.md), estimated impact and next steps toward production
