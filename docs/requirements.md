# Requirements

These describe what the current build actually does, written up after the fact rather than gathered from a stakeholder upfront, since this was a self-directed project. They're included here to show the thinking behind the build in a format closer to how a real piece of work would be scoped and documented.

## Functional requirements

**FR01.** A user shall be able to select a product from the catalogue to inspect.

**FR02.** The system shall calculate a sales-gap anomaly score for the selected product, based on its historical sales velocity and the elapsed time since its last sale.

**FR03.** The system shall classify the result as Normal, Warning, or Critical, based on where the anomaly score falls relative to a configurable threshold.

**FR04.** The system shall explain, in plain language, why a product received its classification, rather than showing only a raw score.

**FR05.** A user shall be able to adjust the sales velocity, the length of the sales gap, and the alert threshold, and see the result update accordingly.

**FR06.** The system shall display a small worklist showing the selected product alongside two neighbouring products in the catalogue, each with its own classification.

## Non-functional and usability requirements

**NFR01.** A user without a statistics background should be able to understand the result and what action it suggests, without needing to interpret a raw probability.

**NFR02.** The system should load and respond to slider adjustments without a noticeable delay, so exploring different scenarios feels immediate rather than sluggish.

**NFR03.** Any figure shown that is simulated rather than measured, shelf location, unit price, revenue estimate, should be visibly labelled as such at the point it's displayed, not only in separate documentation.

## Business rules

**BR01.** Critical status is assigned when the anomaly score meets or exceeds the configured threshold. Warning status is assigned when the score falls within 15 percentage points below that threshold. Anything below that band is treated as Normal.

**BR02.** A minimum monitoring velocity may be applied to slow-moving products so they can still trigger an alert within a reasonable timeframe. This floor is a monitoring decision, not a correction to the observed data, the true observed velocity is always preserved separately.

**BR03.** Stock codes representing administrative entries rather than physical products, postage, bank charges, and similar, are excluded from the catalogue entirely, since they can never be the subject of a shelf check.

**BR04.** The trading-hours window used to calculate sales velocity is derived from the same filtered subset of data it's applied to, not from a broader dataset that may not reflect the same patterns.
