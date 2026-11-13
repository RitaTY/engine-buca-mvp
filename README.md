# Engine · Initiative prioritization and Lean BuCA (MVP prototype, v3)

A clickable prototype of one workflow for Customer Services portfolio intake: an employee submits an initiative, the system checks quality and strategic fit, Business Control validates a Lean Business Case (BuCA), the Heads decide, capability leads commit capacity, and delivery closes the loop.

> **Prototype.** All initiatives, OKRs, Finance rules and team capacities in this repo are **made up** for testing. Don't use it with real customer data.

## v3: three steps, two roles

v3 simplifies v2 after PO feedback (see `docs/v3-plan.md`). Only the first four artifacts are in use, in three steps:

| Step | What happens | Who |
|---|---|---|
| 1 Idea + outcome | One card: the problem, the KPI that should move (baseline, target, date, how it is measured) and a rough size S/M/L | Owner |
| 2 Triage | Accept (with a Run/CI/Change label), merge, send back or decline | Reviewer · PO decides; Reviewer · Finance and Reviewer · Product lead advise |
| 3 Business case | Lean BuCA, built by the owner and approved by Business Control | Owner, Reviewer · Finance |
| 4 Hand-off to Aha! | The Engine builds an Aha! initiative (preview, *Copy for Aha!*, API payload). The PO creates it in Aha! and records the reference. From there the B2C operating model takes over. | Reviewer · PO |

The data model still has 8 stages, so Decide, Capacity, Deliver and Review can come back later. Internally: step 1 = stage 1, step 2 = stage 2, step 3 = stage 4 (stage 3 is merged into step 1; old stage-3 items move to stage 4), step 4 = stage 5 and up.

## Where the Engine fits

The B2C Product Operating Model starts at *Initiative + business case* in Aha!. The Engine is the front door before that: it turns a frontline problem into an Aha!-ready initiative with a measurable outcome and a comparable Lean BuCA, then hands it off. Prioritising, capacity, delivery and review happen in Aha! and the operating model's ceremonies, not in the Engine.

**Aha! hand-off today:** copy and paste, then record the Aha! reference (for example CS-S-12) and link. The API payload matches Aha!'s *Create an initiative* call (`POST /api/v1/products/:product_id/initiatives`); the custom fields need matching fields in the Aha! workspace. **Next:** a Power Automate flow that sends the payload with an Aha! API key kept in the flow (never in this page) and writes the reference back.

## What's in the app

- **Navigation**: Pipeline · New idea · Parameters (Parameters for Reviewer · Finance only).
- **Roles**: Owner, Reviewer · PO, Reviewer · Finance, Reviewer · Product lead. Switch at the top right.
- **Pipeline** with three views. **All ideas** (default): every open idea in one grid, each card showing its step, size, label and status; at triage the PO drags one idea onto another to bundle them. **Buckets**: the team adds, renames and removes its own buckets and drags ideas into them (or uses *Move to…*). Buckets are shared, start empty, and don't change an idea's step. **Table**: every idea, including declined and merged ones, for comparing. **Sort by** step, size, label (Run/CI/Change), status, OKR, source, KPI, waiting longest or newest; **Needs my action** filters; search by ID or name.
- **Triage advice**: Finance and the product lead mark *Supports* or *Has concerns* (note required). The PO sees the advice in the triage decision and on the card, and can decide without it.
- **Lean BuCA** with a lever library (avoided contacts, shorter handling time, fewer repeat contacts, lower contact ratio, less manual work, lower external cost, fewer customers lost), typed **cost lines** (FTE, licence, advisory, hardware, other; one-off or recurring; start year; CAPEX/OPEX) and a short / standard / long investment horizon. Results per year, CAPEX/OPEX split, and "Show the sum".
- **Parameter library** (Business Control): price per FTE (customer service and delivery), cost per contact, paid hours, shrinkage, occupancy, contact ratio, AHT per queue, realisation, horizon, margin, CAPEX threshold. Every change has a valid-from date, a reason and who made it.
- **Photo moment**: approving a Lean BuCA freezes the parameters it used. Later parameter changes don't touch it; Business Control can recalculate with today's parameters (reason required), which takes a new photo moment.
- **Versions**: a new BuCA version on every send, return, approval and recalculation, with a side-by-side comparison of assumptions, parameters and results.
- **Logged overrides**: Business Control can override any parameter or assumption for one case. A reason is required; who, when, old value and new value are logged.
- **CAPEX/OPEX check**: flags recurring CAPEX, licence or advisory CAPEX, one-offs below the CAPEX threshold, and capitalised effort on Run/CI work (example rules, for Business Control to confirm).
- **Traceable history**: every entry links to its step (`#i-<id>-a<step>`, step 1-4).
- Initiative IDs (`ENG-101` …), searchable on the pipeline.
- **English and Dutch** (EN | NL at the top right, remembered per browser). English is the source; Dutch is applied on screen from a phrase table with patterns for texts that contain numbers or names, so stored data never changes language. Framework terms stay English in both: stage and artifact names, role titles, Run/CI/Change, Fund/Prove first/Queue/Stop. Example data and typed-in text are not translated. Claude answers in Dutch when NL is on.

## How it runs

One self-contained `index.html`: vanilla JavaScript, no build step, no dependencies. Styling follows the Eneco web style brief (Nunito Sans as a stand-in for Etelka, no Eneco logo).

It is published as a Claude artifact and uses three artifact capabilities:

| Capability | Used for | Without it |
|---|---|---|
| `db` | Shared board: `cfg/main` (rules, OKRs, teams, cycle, relationships, buckets) and one document per initiative in `items/` | Falls back to this browser's `localStorage` |
| `user` (`profile` scope) | Names in the history; only opaque user ids are stored | History shows roles only |
| `sample` | Claude quality/fit check and relationship suggestions | Rule-based check; no Claude suggestions |

Open `index.html` directly in a browser to run it in local mode with the example data.

### Example data

`seed/example-data.json` holds the shared-board documents (`cfg/main` and `items/*`). On the published artifact, load it with `db_write`, or use **Reset example data** as page owner (two clicks, replaces all shared data).

## Tests

End-to-end tests use Playwright against a fake shared database (`tests/fake-db.js`, backed by `localStorage` so two tabs act as two testers).

```bash
pip install playwright && playwright install chromium
python3 tests/test_v3.py             # v3 journeys: pipeline, table, idea card, triage advice, PO decision, ready for decision, Dutch
python3 tests/test_shared_board.py   # two testers, live sync, drag-to-bundle on the pipeline, levers
python3 tests/test_finance.py        # parameter library, photo moment, versions, overrides, CAPEX/OPEX
```

Screenshots are written to `tests/screenshots/` (ignored by git).

## Known limitations

- Parameter values, AHT baselines and CAPEX/OPEX rules are **examples**. Business Control should replace and confirm them.
- Owners' own edits between versions are captured in the version comparison, not one by one. Business Control overrides and parameter changes are logged individually.
- Benefits start in year 1 at full size (no ramp-up), and the net value is not discounted (no NPV).
- OKRs are placeholders; the similarity score is plain word overlap.
- The Dutch was written by Claude and still needs a check by a native speaker.
- Last write wins when two people edit the same initiative at the same moment.
- Not connected to ADO, Aha, Power BI or Teams (the ADO push is simulated).

## Roadmap

1. Claude-based similarity and a warning before unlikely bundles
2. Benefit ramp-up per year and an optional NPV with a Finance discount rate
3. Server-side checks so only the right role can take each step
5. Connections to ADO/Aha, Power BI (baselines, AHT) and Teams notifications
