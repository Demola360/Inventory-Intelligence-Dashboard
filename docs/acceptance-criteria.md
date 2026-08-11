# Acceptance Criteria

These are tied to observable behaviour in the live application, not generic statements. Each maps to a requirement already documented in `requirements.md`.

## AC01, Critical classification and worklist inclusion

**Given** a product's anomaly score is at or above the Critical Alert Threshold
**When** the assessment is displayed
**Then** the product's status shows as Critical, and it appears in the Priority Worklist if it ranks among the top five scores for that scenario

## AC02, Warning band

**Given** a product's anomaly score falls within 15 points below the Critical Alert Threshold
**When** the assessment is displayed
**Then** the product's status shows as Warning, not Critical or Normal

## AC03, Normal classification

**Given** a product's anomaly score is more than 15 points below the Critical Alert Threshold
**When** the assessment is displayed
**Then** the product's status shows as Normal, and no Recommended Action section is displayed

## AC04, Threshold slider changes classification live

**Given** a product is currently classified Warning
**When** the user lowers the Critical Alert Threshold slider until it sits at or below the product's current anomaly score
**Then** the product's status updates to Critical without needing a page reload

## AC05, Hours-without-sale slider changes worklist scores

**Given** the Priority Worklist is displayed
**When** the user changes the "Current Hours with Zero Sales" slider
**Then** each product currently shown in the Priority Worklist has its Anomaly Score recalculated to reflect the new value

## AC06, Assumed velocity only affects the selected product

**Given** a product is selected and its Assumed Sales Velocity slider is changed
**When** the Priority Worklist is checked
**Then** the worklist rankings are unaffected, since the worklist uses each product's own Monitoring Velocity, not the single-product slider

## AC07, Observed vs Monitoring velocity stays distinct

**Given** a product whose real historical sales rate is below the 0.2 units/hour floor
**When** the sidebar caption is displayed
**Then** the Historical rate shown reflects the true observed rate, and the Monitoring baseline shown reflects the floor-adjusted rate, as two distinct values

## AC08, Recommended Action visibility

**Given** a product is classified Critical
**When** the assessment is displayed
**Then** the Recommended Action section appears, showing a shelf location and a revenue exposure figure
