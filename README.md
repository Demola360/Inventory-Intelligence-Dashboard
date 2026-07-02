## Inventory Intelligence Dashboard

**An early-warning system for "missing" inventory that may not actually be on the shelf.**
*Online Retail dataset used for this project and was obtained from https://archive.ics.uci.edu/dataset/352/online+retail.*
---

## The Phantom Inventory Problem

A Phantom inventory is one that appears in a company's computer system but is physically absent from the shelf due to issues such as misplacement, inventory errors, damage, shrinkage or possible theft
Imagine you manage a retail store, product hasn't sold in 6 hours. Is that normal? Maybe it's just a slow product, or a quiet time of day or is something wrong? Maybe it's been stolen, misplaced on the wrong shelf, or the listing is broken online. 
In the fast paced world of today, walking the floor to manually check every slow-moving item wastes staff time and is labour intensive, but ignoring the problem means lost sales sitting on a shelf nobody can find.

This dashboard tackles that problem with statistics instead of guesswork. It asks one question for any product: *given how fast this item normally sells, how unusual is it that we've seen zero sales for this many hours?* If the answer is "extremely unusual," the item gets flagged for a human to go check.

---

## How it works 

1. The system looks at historical sales data and works out how fast each product typically sells, in units per hour.
2. Compares this to how many hours it's been since the last sale.
3. Using a well-established statistical model (explained below), the dashboard calculates the probability that this period of 'lack of sale' could happen naturally for a product selling at that normal rate.
4. If that probability is low enough, the item is marked as a likely phantom inventoty issue and added to a prioritized worklist for floor staff to physically check.

---

## What's in the demo dashboard
1. The dashboard uses dynamic simulation sliders to manually adjust the sensitivity, the sales rate, and the time elapsed to show how the system responds to varying situations which mimics live data situations.
2. A curated set of example products is loaded by default, chosen deliberately from the dataset to show three different behaviors side by side: a slow-moving item, a medium-moving item near the alert threshold, and a fast-moving item that triggers an alert almost immediately. This makes the logic easy to follow.
3. An "Explore Full Catalogue" option is available in the sidebar to demonstrate how the model is model applied across the entire underlying dataset rather than just the curated examples.
4. The underlying dataset is a publicly available dataset. It has been filtered to United Kingdom transactions only, treating that subset as a stand-in for a single store branch, since the original dataset has several locations.
5. A simulated worklist shows how this mimics a real operational workflow: prioritized tasks, complete with a fictional aisle/shelf location, automatically generated for staff to act on.

---

## Why the Poisson distribution?

The Poisson distribution is the standard statistical tool for modeling the number of times an event happens in a fixed window, when those events occur independently and at a roughly constant average rate. A sales transaction landing in a given hour fits that description reasonably well, which makes Poisson a natural fit here for a few reasons:

1. It directly answers the question being asked. The dashboard is showing "how unlikely is this specific length of time without sales?". The Poisson distribution is purpose-built for exactly that kind of question (the probability of zero events occurring in a given window).
2. It needs very little data to work. Many more sophisticated forecasting models (Negative Binomial, ARIMA, machine learning regressors, etc.) need large volumes of clean, regularly-spaced historical data per item to train reliably. Poisson only needs a single number, the average rate, which makes it practical even for newer or lower-volume products where richer models would be unreliable or simply unusable.
3. It is easily interpreted and every output is a probability. But for this dashboard, the probabilty is converted to a percentage confidence. A store manager may find it diffcult to understand "there's a 2% chance this is not a normal sale pattern" but the cofidence bar shows a "98% chance that there is an issue," which makes it easier to understand by non-technical staff.
4. Poisson and Poisson-derived methods are commonly used in real anomaly detection and quality-control settings (for example, flagging unusually quiet sensors or unusually low event counts), so the choice mirrors established practice rather than being a novel or unusual one for this dashboard.

---

## Limitations 

The key limitations of this approach are:

1. Built on historical averages, not live conditions.** The "normal" sales rate is calculated from past data. Real-world demand for a product can shift week to week or season to season, so a rate that was accurate last month may no longer reflect today's reality.
2. A statistically unusual sales gap means a human should go check the shelf, it does not, by itself, confirm theft, misplacement, or any specific cause. The dashboard is designed to direct attention efficiently, not to replace a physical investigation.
3. A genuine spike or genuine dip in demand caused by a sale, a marketing push, or a competitor's pricing would look statistically identical to a phantom stock event in this model, since the model has no awareness of external campaigns.
4. Poisson assumes events happen independently of each other at a steady average pace. Real retail sales are often "bursty" (for example, several people buying the same item in quick succession after seeing it on social media), which the model wasn't built to account for.
5. The model doesn't currently distinguish between close of business where no sale is expected and peak sales days. A more advanced version could build in time-of-day or day-of-week baselines rather than a single flat average.
6. The aisle/shelf locations and the live worklist shown in the demo are simulated for illustration purposes; they are not connected to a real warehouse management system.

---

## Why these limitations are included on purpose

This project is built as a portfolio demonstration of statistical and analytical thinking, not a plug-and-play production system. Being explicit about a model's assumptions and blind spots is, in my view, just as important as the model itself. 

---

## Tech stack

- Python where the program was built.
- Streamlit for the interactive dashboard interface
- Poisson distribution (scipy.stats) as the statistical core of the anomaly detection logic
