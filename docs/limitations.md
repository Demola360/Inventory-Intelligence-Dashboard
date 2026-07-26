# Limitations

No model is the full picture. The key limitations of this approach are:

1. **Built on historical averages, not live conditions.** The "normal" sales rate is 
calculated from past data. Real-world demand can shift week to week or season to season, 
so a rate accurate last month may no longer reflect today.

2. **A statistically unusual gap means a human should check the shelf, not proof of a 
specific cause.** It does not, by itself, confirm theft, misplacement, or any specific 
issue. The dashboard directs attention efficiently, it doesn't replace physical investigation.

3. **No ground-truth validation.** There's no labelled set of confirmed phantom-stock events 
to test the model's accuracy against, so it isn't currently possible to say what proportion 
of flagged items would turn out to be real issues versus false alarms. A production version 
would need a feedback loop where staff log the outcome of each check, so the model's 
real-world hit rate could be measured and the threshold tuned accordingly.

4. **Genuine demand spikes or dips look identical to phantom stock.** A promotion, marketing 
push, or competitor pricing change would produce the same statistical signature as a real 
inventory problem, since the model has no awareness of external campaigns.

5. **Poisson assumes steady, independent events.** Real retail sales are often bursty, several
 purchases in quick succession after a social media mention, for example, which this model 
 doesn't account for.

6. **No time-of-day or day-of-week baseline.** The model uses one flat average across the whole 
trading day, so it can't currently distinguish a quiet mid-afternoon lull from a quiet peak-hour 
gap. A more advanced version could build in hourly or daily baselines.

7. **Shelf locations and revenue figures in the demo are simulated**, for illustration only, not 
connected to a real warehouse or pricing system.

## Why these limitations are included on purpose

This project is a portfolio demonstration of statistical and analytical thinking, not a 
plug-and-play production system. Being explicit about a model's assumptions and blind spots 
is just as important as the model itself.
