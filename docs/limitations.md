# Limitations

The proof of concept has the following limitations.

1. **Built on historical averages, not live conditions.** The velocity used is calculated from past data. Real-world demand can shift week to week or season to season, so a rate accurate last month may no longer reflect today.

2. **A statistically unusual gap means a human should check the shelf, not proof of a specific cause.** The dashboard helps direct attention; it does not replace physical investigation.

3. **No ground-truth validation.** There's no labelled set of confirmed phantom-stock events to test the model's accuracy against, so it isn't currently possible to say what proportion of flagged items would turn out to be real issues versus false alarms. A production version would need a feedback loop where staff log the outcome of each check, so the model's real-world hit rate could be measured and the threshold tuned accordingly.

4. **The model cannot distinguish inventory issues from changes in demand.** Promotions, seasonality, pricing changes, or shifts in customer behaviour can change the expected sales pattern without any inventory discrepancy, and would produce the same statistical signature as a real issue.

5. **Poisson assumes steady, independent events.** Real retail sales are often bursty, several purchases in quick succession after a social media mention, for example, which this model doesn't account for.

6. **No time-of-day or day-of-week baseline.** The model uses one flat average across the whole trading day, so it can't currently distinguish a quiet mid-afternoon lull from a quiet peak-hour gap.

7. **Every product shares the same observation-period denominator.** Velocity is calculated using the full catalogue's operational hours as the denominator for every SKU, which assumes each product was available and sellable throughout the entire observation period. A product introduced, discontinued, or temporarily unavailable during that period would have its historical rate understated or overstated as a result.

8. **The source data wasn't collected for physical inventory monitoring.** The underlying dataset is online transaction history, not shelf availability, stock-on-hand, or confirmed inventory discrepancies. The UK subset is deliberately repurposed as a fictional branch to demonstrate the concept, not a representation of a real store's operations.

9. **Shelf locations and revenue figures in the demo are simulated**, for illustration only, not connected to a real warehouse or pricing system.

## POC scope

These limitations reflect the deliberate scope of the proof of concept. Addressing them would require additional data, stakeholder input, and real-world testing.