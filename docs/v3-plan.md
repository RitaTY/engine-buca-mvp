# Engine v3 — plan (not built yet)

Based on the PO's feedback on v2 (12 Nov 2026). **Built on the `v3` branch** (13 Nov 2026); `main` still serves v2 until the merge.

## What changes, and why

| PO feedback | v3 decision |
|---|---|
| Too complicated; only the first four artifacts for now | Build only demand + outcome, triage, Lean BuCA. Stages 5–8 are **hidden, not deleted** (data model keeps 8 stages). |
| Merge intake and KPI measurement into one first step | One card: idea + outcome. The separate outcome check by the portfolio lead goes away; measurability becomes a triage checklist item. |
| Triage evaluated by Business Control (Finance), PO and product lead | Joint triage. **The PO decides**; Finance and the product lead advise, and their input is logged. |
| Clear navigation; see all ideas in one place to decide | Triage happens **inside the Pipeline**. No separate triage page. |
| Business case before or after triage? | **After.** Triage bundles demand into initiatives (a BuCA is per initiative) and sets the investment type (only Improvement uses the Lean BuCA). |

## v3 flow

| # | Step | Who | Gate to move on |
|---|---|---|---|
| 1 | **Idea + outcome** (one card) | Owner | Problem, who/how often, KPI + baseline, target, **rough size S/M/L** |
| 2 | **Triage** (on the Pipeline) | Reviewer (PO decides; Finance + product lead advise) | Accept with a Run / CI / Change label · Merge · Send back · Decline |
| 3 | **Lean BuCA** | Owner builds, Reviewer (Business Control) approves | Approved → **Ready for decision** |

"Ready for decision" is the end state in v3.

**Rough size (step 1):** the owner picks S (under €50k per year), M (€50k–250k) or L (over €250k), labelled "Estimate, not a business case". It gives Finance something to judge at triage without asking owners to build a BuCA first. (Built as a choice, not a calculation, to keep step 1 short.)

## Roles

Only two roles, with general names:

- **Owner**: brings in the idea, fills in the card, builds the Lean BuCA.
- **Reviewer**: triages and approves. Reviewers can carry a label (PO / Finance / Product lead) so the log shows who said what; only the PO label can make the triage decision, and only the Finance label can approve the BuCA.

## Navigation

Three items: **Pipeline · New idea · Parameters** (Parameters visible to Finance reviewers only).

- **Pipeline** columns: Idea → Triage → Business case → Ready for decision.
- Two views: **Board** (flow) and **Table** (compare: rough size / value, KPI, OKR fit, days waiting). Table is the decision view for the PO.
- **Needs my action** is a filter on the Pipeline, not a page.
- Triage actions and bundling (drag a demand card onto another) happen on the card in the Triage column.
- Removed for now: Calendar, Decision agenda, Capacity view, role-picker page (replaced by a simple Owner / Reviewer switch).

## Open questions

1. Step 1 gets longer. Should the KPI be chosen from a list linked to the OKRs, with "I don't know the baseline — ask an analyst" allowed? (Not decided.)
2. Finance at every triage: kept as planned for now; revisit if it becomes a bottleneck.
3. PO walkthrough of the new Pipeline before building (planned 14 Nov).

## Release plan (keeps the shared Vercel link stable)

1. Build v3 on the `v3` branch. Vercel gives every branch its own **preview URL**; the link already shared (production, from `main`) keeps showing v2.
2. Test v3 on the preview URL (PO walkthrough, Finance check).
3. When approved, merge `v3` into `main`. Vercel redeploys production automatically: **same link, now v3**.
4. Before merging, tag the current version (`v2`) so it can be restored in one step if needed.

Note: v3 keeps its browser data under a new key (`engine-buca-v3`), so testers start with the v3 example data. v2 example data lives in the page's own database/seed. Check whether v3's changed stage model needs a fresh seed before the merge.
