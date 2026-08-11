# UAT-Style Test Scenarios

Test scenarios run personally against the live application. Each ties to one or more acceptance criteria in `acceptance-criteria.md`. These are self-conducted, not formal UAT signed off by a business representative, and are labelled accordingly.

## Scenario 1, Critical SKU classification and worklist inclusion

**Steps:** Select a curated product known to score above the default 95% threshold at the default 3-hour setting.
**Expected result:** Status shows Critical. If the product's score ranks among the top five in the catalogue for the current scenario, it appears in the Priority Worklist.
**Covers:** AC01

## Scenario 2, Threshold slider reclassifies a product live

**Steps:** Select a product currently showing Warning. Drag the Critical Alert Threshold slider down until it's at or below the product's current score.
**Expected result:** Status changes from Warning to Critical without a page reload.
**Covers:** AC04

## Scenario 3, Hours-without-sale slider updates the worklist

**Steps:** Note the five Anomaly Scores in the Priority Worklist. Change the "Current Hours with Zero Sales" slider from 3 to 20.
**Expected result:** All five scores increase, since raising the shared hours value raises every product's expected score under the model. The five SKUs shown do not change, because the worklist applies one hours value uniformly to the whole catalogue, which makes ranking mathematically equivalent to ranking by velocity alone, unaffected by the hours value itself.
**Covers:** AC05

## Scenario 4, Assumed velocity slider stays scoped to the selected product

**Steps:** Select a product. Drag its Assumed Sales Velocity slider to the maximum. Check the Priority Worklist.
**Expected result:** The worklist's five ranked products and their scores are unchanged by this action.
**Covers:** AC06

## Scenario 5, Velocity floor stays visible for a very slow product

**Steps:** Select Queen of the Skies Holiday Purse (or another product with observed velocity near zero).
**Expected result:** Historical rate displays as approximately 0.00 units/hr, Monitoring baseline displays as 0.20 units/hr, the two values are shown separately, not merged.
**Covers:** AC07

## Scenario 6, Edge input, minimum hours without sale

**Steps:** Set "Current Hours with Zero Sales" to its minimum value, 1 hour.
**Expected result:** The app does not error. All products show low anomaly scores relative to their values at higher hour settings, and the app remains fully interactive.
**Covers:** general input robustness, supports AC04 and AC05

## Scenario 7, Classification boundaries

**Steps:** Using a single product, adjust its anomaly score, via the velocity or hours sliders, to land at three points in turn: exactly at the Critical threshold, exactly 15 points below it, and more than 15 points below it.
**Expected result:** Status reads Critical at or above the threshold, Warning within the 15-point band below it, Normal beyond that.
**Covers:** AC02, AC03
