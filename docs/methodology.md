# Methodology

## How the model works

Given a product's assumed sales rate, how unusual would it be to observe zero sales over a specified period? That's the one question this model answers.

To answer it, the model calculates Lambda (λ), the number of sales expected in a given time frame. Sales velocity is how many units a product historically sells per hour, this models unit quantity as the count of interest, not transaction frequency, one customer buying six units in a single transaction counts as six toward this rate, not one.

**λ = Sales Velocity × Hours**

The output is the probability of zero sales. The dashboard converts this into an anomaly score, which flips the probability so it's easier to interpret. For example, if the model says there's a 5% chance the period of no sales is normal, the anomaly score is 95%, meaning this length of no sales is statistically unusual and worth checking. This is a decision-support measure, not a calibrated probability that stock is physically missing. The result is a colour-coded verdict, Normal, Warning, or Critical, so staff can act on it without needing to understand the statistics behind it.

## Why the Poisson distribution

Poisson is the standard tool for modelling how many times an event happens in a fixed window, when those events occur independently at a roughly constant average rate.

- It directly answers the question being asked, how unlikely is this specific length of time without sales.
- It needs very little data to work, just one number, the average rate, which makes it usable even for lower-volume products.
- It converts naturally into a percentage, easier for non-technical staff to act on than a raw probability.
- It mirrors established practice in anomaly detection and quality-control settings.

This is an interpretable baseline for converting historical demand and elapsed time into an indication of unusual sales inactivity, not a claim that it's the most sophisticated model available. The constant-rate and independence assumptions it relies on are examined in [limitations](limitations.md).

## Discovering the trading hours from the data itself

Rather than assuming a trading window, the hour was extracted from each invoice date and transactions were counted per hour, on the UK-filtered subset specifically, since the window needs to be justified against the same data it's applied to, not a broader international dataset that may follow a different pattern.

| Hour | Transaction Volume (UK only) |
|---|---|
| 06:00 | 1 |
| 07:00 | 214 |
| 08:00 | 6,405 |
| 09:00 | 17,175 |
| 10:00 | 31,152 |
| 11:00 | 43,734 |
| 12:00 | 65,025 (Peak) |
| 13:00 | 56,916 |
| 14:00 | 47,515 |
| 15:00 | 40,738 |
| 16:00 | 21,952 |
| 17:00 | 11,877 |
| 18:00 | 2,716 |
| 19:00 | 3,005 |
| 20:00 | 778 |

Activity is negligible before 07:00 and after 20:00, supporting a 06:00 inclusive to 20:00 exclusive simulation window, 14 hours, based on the observed transaction activity in this dataset, not confirmed physical store opening hours.

## Synthetic model behaviour checks

Since no labelled phantom-inventory events exist for this dataset, the implementation was checked rather than validated in the strict sense. Checking that scores increase monotonically as an injected gap grows confirms the formula was implemented correctly, it doesn't confirm the model correctly identifies real phantom inventory, which would require labelled outcomes this project doesn't have. See `validate_model.py`.

Checked against a product selling 0.3 units/hour on average:

| Injected Period of No Sales (hrs) | Anomaly Score |
|---|---|
| 1 | 25.92% |
| 2 | 45.12% |
| 3 | 59.34% |
| 4 | 69.88% |
| 6 | 83.47% |
| 8 | 90.93% |
| 12 | 97.27% |
| 24 | 99.93% |

Scores increase monotonically as expected. Faster-selling products reach high anomaly scores much sooner than slow-moving ones, reflecting the model judging each product against its own normal selling rate rather than applying one flat rule.

## Workload sensitivity by threshold

The 95% Critical threshold used by default in the app is a reasonable starting point, not an empirically calibrated one. Running the real catalogue through a range of candidate thresholds at the dashboard's actual default gap, 3 hours, shows how the size of the resulting worklist changes:

| Threshold | Products Flagged | % of Catalogue |
|---|---|---|
| 80% | 445 | 12.2% |
| 85% | 374 | 10.3% |
| 90% | 298 | 8.2% |
| 95% | 215 | 5.9% |
| 99% | 111 | 3.1% |

A lower threshold generates a larger investigation worklist and increases sensitivity to unusual gaps. A higher threshold produces a smaller, more selective one. Which alerts turn out to be genuine issues cannot be determined without confirmed shelf-check outcomes, so this is workload sensitivity, not a measure of accuracy. See [limitations](limitations.md).

## Key decisions made

1. **UK filter.** Filtered to only United Kingdom transactions, treated as one fictional branch for this simulation. Without this filter, the single-branch simulation breaks down.

2. **14-hour trading window.** Derived empirically from the UK-only hourly transaction distribution above, rather than assumed.

3. **Curated default catalogue.** Six items selected to show two examples from each alert tier, Normal, Warning, and Critical, at default settings, so a first-time visitor sees the full range of outcomes without scrolling through the full catalogue.

4. **Monitoring velocity floor of 0.2.** I set this so a rarely-selling product still gets flagged within a working shift instead of taking weeks. Nobody signed off on 0.2 specifically, it's my number. In a real project I'd take it to the inventory manager and ask what floor actually makes sense given how often staff can realistically check the slowest movers. The true observed velocity is kept separately in the `Observed_Velocity` column so this adjustment stays visible rather than hidden.
