# Business Case

## Business problem

Recorded inventory can differ from what's physically on the shelf, while checking every product manually to catch that is too resource-intensive to do well.

## Objective

Explore whether historical sales behaviour can help prioritise which products are worth investigating, so that limited staff time goes toward the products most likely to need it.

## Stakeholders

**Primary user.** Store or inventory staff performing the physical checks.

**Operational stakeholder.** A store manager deciding whether the resulting workload is manageable day to day.

**Business stakeholder.** An inventory or retail operations manager interested in stock accuracy and lost-sales risk.

**Technical stakeholder.** Whoever would be responsible for connecting this to live point-of-sale and inventory systems in a real deployment.

## What the model actually flags today

At the dashboard's actual default settings, a 3-hour gap and a 95% threshold, running the model across the full catalogue flags approximately 215 products as Critical, 5.9% of the catalogue. At a 99% threshold, that drops to 111 products, 3.1%. Both figures come directly from `validate_model.py`. Whether 215 checks a day is realistic isn't something I can answer from this data, it depends on how many staff are on shift and how long each check actually takes. That's a conversation with the store manager, not a modelling decision.

## A future operating target, not a current result

A production implementation would need an agreed investigation-capacity target, defined with store operations, rather than one set by the model itself. For illustration, a target of 1 to 2% of the catalogue would represent roughly 36 to 72 products in a 3,600-SKU catalogue, tighter than the current default, and reaching it would mean raising the threshold further, adding time-of-day awareness, or using real feedback data to separate genuine anomalies from ordinary slow sellers more precisely than a single flat threshold can. None of that tuning has happened yet, so this stays an illustration, not a target this build has been calibrated to hit.

## Current process (illustrative)

Inventory discrepancy occurs, the system continues to show stock as available, the issue may go unnoticed, and it's typically only discovered when a customer or staff member happens to encounter it, or through an occasional manual audit.

## Proposed process

A sales gap becomes statistically unusual, the product enters a prioritised worklist, staff investigate, and the outcome is recorded, found in place, misplaced, missing, damaged, or unable to confirm, so the inventory record can be corrected, the item returned to place, written off, or escalated accordingly.

## Potential benefits

**Operational efficiency.** Prioritising checks rather than treating every SKU equally.

**Stock accuracy.** Surfacing potential discrepancies earlier than an occasional manual audit would.

**Customer experience.** Reducing the risk of a system showing a product as available when it isn't on the shelf.

**Decision quality.** Converting raw transaction history into an actionable investigation signal rather than leaving staff to notice gaps by chance.

These are hypothesised benefits based on the concept, not outcomes measured from this POC.

## Assumptions, constraints, and risks

**Assumptions.** Sales inactivity contains useful information about stock availability. Investigation capacity exists to act on flagged items. Transaction timestamps are recorded with sufficient timeliness to be useful.

**Constraints.** No labelled outcomes exist yet to confirm accuracy. The dataset is static and historical, not a live feed. There's no current connection to real inventory records, so the model can't yet distinguish a product that's genuinely out of stock in the system from one the system still shows as available.

**Risks.** Alert fatigue if the worklist is too large for available staff time. An inaccurate baseline rate producing misleading scores for products with unusual histories. Unnecessary checks eroding staff trust in the tool. Demand patterns changing in ways the model doesn't adapt to. Users treating an anomaly score as confirmation of a problem rather than a prompt to check.

## Pilot success measures

A future pilot would need its own success measures, not the same numbers used to describe this POC.

**Operational.** Alerts generated per shift. Average investigation time. Percentage of alerts actually investigated. Time from alert to resolution.

**Model and business.** Percentage of flagged checks that identify a real issue. Percentage of known discrepancies the system actually catches. Stock-record corrections generated as a result. Estimated sales or margin protected.

None of these have values yet, defining what would be measured is the point at this stage, not producing numbers this POC has no way to generate honestly.

## From proof of concept to production

A production version would need a few things this build deliberately leaves out.

**Live point-of-sale data**, so alerts reflect what's actually happening on the shelf right now rather than what historically should be happening.

**Live inventory records.** Right now the model has no visibility into what the inventory system currently believes about a product's stock level. Without that, it risks flagging products the system already correctly shows as zero stock, which isn't phantom inventory, it's just an accurate record. A real deployment needs to know the system believes stock is available before treating a sales gap as suspicious.

**Awareness of discounts, promotions, and seasonality**, so a product selling well above its normal rate during a promotion doesn't distort its baseline for future comparisons.

**A staff feedback loop**, recording the outcome of each check, which is also the only way to responsibly move the threshold toward a tighter target without just guessing.

## Next steps

Pilot the current logic against a small, real product set. Collect real check outcomes. Use those outcomes to calibrate the threshold and test whether a higher threshold, or a different model entirely, would better separate genuine issues from ordinary slow sellers. Evaluate whether the measured value justifies wider rollout.
