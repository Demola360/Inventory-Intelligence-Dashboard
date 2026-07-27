## What the model actually flags today

At the dashboard's actual default settings, a 3-hour gap and a 95%
threshold, running the model across the full catalogue flags roughly
5.9% of products as Critical (215 out of the catalogue). At a 99%
threshold, that drops to 3.1%. Both figures come directly from
`validate_model.py`, tested at the same 3-hour gap the dashboard
itself defaults to, not an arbitrary scenario.

## A future operating target, not a current result

5.9% is already reasonably close to a genuinely small daily check
list, but a tuned production version could realistically aim tighter
still, toward the highest-priority 1 to 2% of the catalogue, so a
store's daily investigation effort stays small and targeted even as
the catalogue grows.

That 1 to 2% figure is an aspiration for what a tuned, production
version of this system could aim for, not a description of what the
current threshold produces. Getting there would mean raising the
threshold further, adding time-of-day awareness, or using real
feedback data to separate genuine anomalies from ordinary slow
sellers more precisely than a single flat threshold can. None of
that tuning has happened yet, this build hasn't been calibrated
against any real outcome, so the 1 to 2% target stays exactly that,
a target, until there's evidence to support it.
