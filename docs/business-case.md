# Business Case

## Estimated business impact (illustrative)

For a branch carrying roughly 3,600 active SKUs, spot-checking every slow-moving item manually is impractical. If this model correctly narrows daily manual checks down to the highest-confidence 1 to 2% of the catalogue, that's the difference between checking dozens of items a day versus thousands, freeing staff time for other tasks while still catching the gaps most likely to represent a real issue.

This is an illustrative estimate based on catalogue size, not a measured result, given the lack of ground-truth validation noted in the limitations.

## From proof of concept to production

This dashboard was built as a proof of concept using a static historical dataset. A production version would need a few things this version deliberately leaves out.

**Live point-of-sale data**, feeding directly into the model, so alerts reflect what's actually happening on the shelf right now rather than what historically should be happening.

**Awareness of discounts, promotions, and seasonality**, a product selling three times its normal rate during a promotion shouldn't trigger a phantom inventory alert.

**A staff feedback loop**, allowing the system to learn from real check outcomes over time, gradually reducing false positives and giving a real, measured accuracy figure instead of an illustrative one.

## Possible next steps

- Add hourly or day-of-week baselines instead of a single flat velocity
- Build the feedback mechanism to log real outcomes of flagged checks, enabling actual accuracy measurement
- Connect simulated shelf-location and pricing data to a real inventory system
