# Business Case

## What the model actually flags today

At the dashboard's default settings, a 95% threshold and a 6-hour gap, running the model across the full catalogue flags roughly 13.5% of products as Critical. That figure comes directly from `validate_model.py`, not from an estimate, it's a measured result of the current threshold against the current data.

## A future operating target, not a current result

A daily check list covering 13.5% of a few thousand products is still a lot of products. A more realistic goal for an eventual rollout would be narrowing that further, toward something like the highest-priority 1 to 2% of the catalogue, so a store's daily investigation effort stays genuinely small and targeted.

That 1 to 2% figure is an aspiration for what a tuned, production version of this system could aim for, not a description of what the current threshold produces. Getting there would mean raising the threshold further, adding time-of-day awareness, or using real feedback data to separate genuine anomalies from ordinary slow sellers more precisely than a single flat threshold can. None of that tuning has happened yet, this build hasn't been calibrated against any real outcome, so the 1 to 2% target stays exactly that, a target, until there's evidence to support it.

## From proof of concept to production

This dashboard was built as a proof of concept using a static historical dataset. A production version would need a few things this version deliberately leaves out.

**Live point-of-sale data**, feeding directly into the model, so alerts reflect what's actually happening on the shelf right now rather than what historically should be happening.

**Awareness of discounts, promotions, and seasonality**, a product selling three times its normal rate during a promotion shouldn't trigger a phantom inventory alert.

**A staff feedback loop**, allowing the system to learn from real check outcomes over time, which is also the only way to responsibly move the threshold toward a tighter target like 1 to 2% without just guessing.

## Possible next steps

- Add hourly or day-of-week baselines instead of a single flat velocity
- Build the feedback mechanism to log real outcomes of flagged checks, enabling actual accuracy measurement
- Use that feedback data to test whether a higher threshold or a different model can responsibly bring the flagged percentage down toward an operational target, rather than raising the threshold blind
- Connect simulated shelf-location and pricing data to a real inventory system
