# MV Futures Signal Scan

A standing horizon scan of the weak signals, strong signals, trends, and drivers most
likely to shape the future of teaching, learning, and schooling.

Published by **MV Ventures** / The Mount Vernon School.
**Live dashboard → https://jcolley8.github.io/mv-futures-signal-scan/**

## How it is made

Every 24 hours at 12:00 PM ET an automated scan sweeps peer-reviewed journals, preprint
servers, government and intergovernmental agencies, university research centres, survey
organisations, think tanks, analyst and industry reports, editorially-governed news and
trade press, and signal-bearing product material — across education *and* adjacent
sectors: AI and cognition, labour and economics, climate and civic life, and emergent
technology. No blogs.

New entries are appended to a cumulative corpus rather than replacing it, so the scan
accrues into a body of evidence over time. Every entry links to its original source for
verification. A workflow in this repo rebuilds and republishes the page about an hour
after each scan.

## How entries are classified

**Likelihood of impact** — *actual* (already measurable), *probable* (strong evidence it
will land), *plausible* (credible pathway), *possible* (conceivable but speculative),
*preposterous* (low-probability, high-impact wildcard worth tracking anyway).

**EPISTEME domain** — **E**ducational, **P**olitical, **I**nteraction with environment
(ecological and environmental forces bearing on schools), **S**ocial, **T**echnological,
**E**conomic, **M**oral/**E**thical. Entries may carry more than one.

**Three Horizons** — H1 continuation of the status quo, H2 disruptive innovation,
H3 complete transformation of how we do things.

Entries are also placed on a 0–2 / 3–6 / 7–10 year timeline of expected material impact
on schools. The scan surfaces five **critical uncertainties**: forces that are both
highly uncertain in how they resolve and highly consequential either way — the axes
worth building scenarios on.

## Files

| File | Purpose |
|---|---|
| `index.html` | The dashboard. Self-contained — no build step, no dependencies. |
| `signals.json` | The cumulative signal corpus. |
| `build_dashboard.py` | Renders the corpus into the dashboard. |
| `logo-src.png` | Brand mark; light and dark variants are derived at build time. |
| `.github/workflows/publish.yml` | Daily fetch, rebuild, and publish. |

To rebuild locally: `python3 build_dashboard.py signals.json index.html`
