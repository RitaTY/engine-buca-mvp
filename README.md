# Engine · Initiative prioritization and Lean BuCA (MVP prototype)

A clickable prototype of one workflow for Customer Services portfolio intake: an employee submits an initiative, the system checks quality and strategic fit, Business Control validates a Lean Business Case (BuCA), the Heads decide, capability leads commit capacity, and delivery closes the loop.

> **Prototype.** All initiatives, OKRs, Finance rules and team capacities in this repo are **made up** for testing. Don't use it with real customer data.

## The process: 8 stages, 8 artifacts

Each initiative builds one artifact per stage. Every artifact has one owner who signs it off, and the next stage opens only when the gate is met.

| # | Stage | Artifact | Owner |
|---|---|---|---|
| 1 | Collect · *Vraag* | Demand record | Initiative owner (VC/VS, CoE, NextGen) |
| 2 | Triage · *Schifting* | Initiative overview | Portfolio lead |
| 3 | Outcome · *Meetbaarheid* | Outcome card | Initiative owner, checked by Portfolio lead |
| 4 | Value · *Calculaties* | Lean BuCA | Business control (Finance) |
| 5 | Decide · *Kiezen* | Decision log | Heads + MT |
| 6 | Capacity · *Kunnen we dit?* | Capacity view | Capability lead |
| 7 | Deliver · *Doorzetten* | Delivery structure | PO / delivery |
| 8 | Review · *Leren* | Closed-loop overview | Portfolio lead |

Automation prepares the work (quality and OKR-fit check, assumption check, delivery structure, relationship suggestions). People make every decision.

## What's in the app

- **Welcome page** for first-time visitors: six role cards (what each role does, where it starts, what is waiting for it). Picking one opens that role's Home; "All roles" next to the switcher brings it back. Deep links skip it.
- **Role switcher** for the six roles, with "Waiting for you" per role and a highlighted *Next step* on every initiative.
- **Pipeline** by stage, and a **Calendar** with start/end, KPI target dates and suggested relationships (competing for capacity, same KPI, similar scope; Claude can suggest dependencies, sequencing and synergies).
- **Triage board**: drag demand records onto an initiative to bundle them (dropdown fallback for touch).
- **Lean BuCA** with a lever library (avoided contacts, shorter handling time, fewer repeat contacts, lower contact ratio, less manual work, lower external cost, fewer customers lost), typed **cost lines** (FTE, licence, advisory, hardware, other; one-off or recurring; start year; CAPEX/OPEX) and a short / standard / long investment horizon. Results per year, CAPEX/OPEX split, and "Show the sum".
- **Parameter library** (Business Control): price per FTE (customer service and delivery), cost per contact, paid hours, shrinkage, occupancy, contact ratio, AHT per queue, realisation, horizon, margin, CAPEX threshold. Every change has a valid-from date, a reason and who made it.
- **Photo moment**: approving a Lean BuCA freezes the parameters it used. Later parameter changes don't touch it; Business Control can recalculate with today's parameters (reason required), which takes a new photo moment.
- **Versions**: a new BuCA version on every send, return, approval and recalculation, with a side-by-side comparison of assumptions, parameters and results.
- **Logged overrides**: Business Control can override any parameter or assumption for one case. A reason is required; who, when, old value and new value are logged.
- **CAPEX/OPEX check**: flags recurring CAPEX, licence or advisory CAPEX, one-offs below the CAPEX threshold, and capitalised effort on Run/CI work (example rules, for Business Control to confirm).
- **Decision agenda** for the Heads, ranked by 3-year net value × confidence × OKR fit, with a capacity signal per initiative.
- **Capacity view** per team: committed, funded, waiting for decision, over capacity.
- **Traceable history**: every entry links to its artifact (`#i-<id>-a<stage>`).
- Initiative IDs (`ENG-101` …), searchable on the pipeline.

## How it runs

One self-contained `index.html`: vanilla JavaScript, no build step, no dependencies. Styling follows the Eneco web style brief (Nunito Sans as a stand-in for Etelka, no Eneco logo).

It is published as a Claude artifact and uses three artifact capabilities:

| Capability | Used for | Without it |
|---|---|---|
| `db` | Shared board: `cfg/main` (rules, OKRs, teams, cycle, relationships) and one document per initiative in `items/` | Falls back to this browser's `localStorage` |
| `user` (`profile` scope) | Names in the history; only opaque user ids are stored | History shows roles only |
| `sample` | Claude quality/fit check and relationship suggestions | Rule-based check; no Claude suggestions |

Open `index.html` directly in a browser to run it in local mode with the example data.

### Example data

`seed/example-data.json` holds the shared-board documents (`cfg/main` and `items/*`). On the published artifact, load it with `db_write`, or use **Reset example data** as page owner (two clicks, replaces all shared data).

## Tests

End-to-end tests use Playwright against a fake shared database (`tests/fake-db.js`, backed by `localStorage` so two tabs act as two testers).

```bash
pip install playwright && playwright install chromium
python3 tests/test_shared_board.py   # two testers, live sync, drag-to-bundle, levers
python3 tests/test_calendar.py       # calendar rows, relationship suggestions, confirm/dismiss
python3 tests/test_history.py        # history deep links, role switch, artifact logging
python3 tests/test_finance.py        # parameter library, photo moment, versions, overrides, CAPEX/OPEX
python3 tests/test_welcome.py        # first-visit role picker, switching, deep links
```

Screenshots are written to `tests/screenshots/` (ignored by git).

## Known limitations

- Parameter values, AHT baselines and CAPEX/OPEX rules are **examples**. Business Control should replace and confirm them.
- Owners' own edits between versions are captured in the version comparison, not one by one. Business Control overrides and parameter changes are logged individually.
- Benefits start in year 1 at full size (no ramp-up), and the net value is not discounted (no NPV).
- OKRs are placeholders; the similarity score is plain word overlap.
- Last write wins when two people edit the same initiative at the same moment.
- Not connected to ADO, Aha, Power BI or Teams (the ADO push is simulated).

## Roadmap

1. Claude-based similarity and a warning before unlikely bundles
2. Benefit ramp-up per year and an optional NPV with a Finance discount rate
3. Server-side checks so only the right role can take each step
4. Dutch (EN | NL)
5. Connections to ADO/Aha, Power BI (baselines, AHT) and Teams notifications
