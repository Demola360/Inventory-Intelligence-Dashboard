# Methodology

## How the model works

The dashboard asks one question: what is the statistical probability that a product with this historical sales rate will 
have zero sales over this given period, likely, or due to an inventory problem that needs investigation?

To answer it, the model calculates Lambda (λ), the number of sales expected in a given time frame. Sales Velocity is how 
many units a product historically sells per hour.

**λ = Sales Velocity × Hours**

The output is the probability of zero sales. The dashboard converts this into an anomaly score, which flips the probability 
so it's easier to understand. For example, if the model says there's a 5% chance the period of no sales is normal, the 
anomaly score is 95%, meaning this length of no sales is statistically unusual and worth checking. This does not confirm 
stock is missing, it flags the item as worth a physical check. The result is a colour-coded verdict, Normal, Warning, or 
Critical, so staff can act on it without needing to understand the statistics behind it.

## Why the Poisson distribution

Poisson is the standard tool for modelling how many times an event happens in a fixed window, when those events occur 
independently at a roughly constant average rate. A sales transaction landing in a given hour fits that description 
reasonably well.

- It directly answers the question being asked, how unlikely is this specific length of time without sales.
- It needs very little data to work, just one number, the average rate, which makes it usable even for lower-volume
  products.
- It's easily interpreted as a percentage, easier for non-technical staff to act on than a raw probability.
- It mirrors established practice in real anomaly detection and quality-control settings.

## Discovering the trading hours from the data itself

Rather than assuming a trading window, the hour was extracted from each invoice date and transactions were counted per 
hour, on the UK-filtered subset specifically, since the window needs to be justified against the same data it's applied to.

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

There's negligible activity before 07:00 and after 20:00, confirming the 06:00 to 20:00, 14-hour trading window 
used to calculate each product's normal sales velocity.

## Model validation

Since no labelled phantom-inventory events exist for this dataset, the model was validated by injecting synthetic sales 
gaps of increasing length for a known product velocity, and confirming the anomaly score rises monotonically as the 
injected gap grows. See `validate_model.py`.

Tested against a product selling 0.3 units/hour on average:

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

This confirms the model responds correctly in the direction it should, even without real-world ground truth to compare 
against. Faster-selling products reach high anomaly scores much sooner than slow-moving ones, reflecting the model 
judging each product against its own normal selling rate rather than applying one flat rule.

## Key decisions made

1. **UK filter.** Filtered to only United Kingdom transactions, treating that subset as one branch of a fictional retail
   store chain. Without this filter, the single-branch simulation breaks down.

2. **14-hour trading window.** Derived empirically from the UK-only hourly transaction distribution above, rather than
   assumed.

3. **Curated default catalogue.** Six items selected to show two examples from each alert tier, Normal, Warning, and
   Critical, at default settings, so a first-time visitor sees the full range of outcomes without scrolling through the
   full catalogue.

4. **Velocity floor of 0.2 (a business decision, not a statistical one).** Products below this rate are monitored using a
   minimum rate of 0.2 units per hour so they still trigger alerts within a reasonable shift, rather than taking days or
   weeks. Their true observed velocity is preserved separately in the `Observed_Velocity` column for transparency.
