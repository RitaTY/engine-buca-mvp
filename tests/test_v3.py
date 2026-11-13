"""v3 journeys: pipeline (board + table), idea card with outcome, triage advice and PO decision,
Lean BuCA approval to 'Ready for decision', roles, navigation and the Dutch switch."""
import os, asyncio
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "screenshots"); os.makedirs(OUT, exist_ok=True)
U = "file://" + ROOT + "/index.html"
fails = []

def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""))
    if not ok: fails.append(name)

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        p = await b.new_page(viewport={"width": 1280, "height": 900})
        errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
        ev = p.evaluate
        role = lambda r: p.select_option("#roleSel", r)
        await p.goto(U); await p.wait_for_timeout(1500)

        # navigation and roles
        check("opens on the pipeline", (await p.inner_text("h1")).strip() == "Pipeline")
        nav = await p.inner_text("nav.main")
        check("owner nav: Pipeline and New idea only", "Pipeline" in nav and "New idea" in nav and "Parameters" not in nav and "Triage" not in nav, nav)
        opts = await ev("[...document.querySelectorAll('#roleSel option')].map(o=>o.textContent)")
        check("four roles: Owner + 3 reviewers", opts == ["Owner", "Reviewer · PO", "Reviewer · Finance", "Reviewer · Product lead"], str(opts))
        cols = await ev("[...document.querySelectorAll('.board .col h4')].map(h=>h.textContent)")
        check("four pipeline columns", len(cols) == 4 and cols[0].startswith("1 Idea + outcome") and cols[3].startswith("4 Ready for decision"), str(cols))
        check("old stages hidden (no stage 6-8 items on the board)", await ev("[...document.querySelectorAll('.board .bc')].length") == 7)
        await p.screenshot(path=OUT + "/v3-1-board.png", full_page=True)
        await role("finance"); await p.wait_for_timeout(200)
        check("finance sees Parameters", "Parameters" in await p.inner_text("nav.main"))

        # table view and filter
        await p.click("text=Table"); await p.wait_for_timeout(300)
        rows = await ev("document.querySelectorAll('table.t tbody tr').length")
        check("table lists all ideas incl. merged/declined", rows == 8, str(rows))
        await p.check("#mineOnly"); await p.wait_for_timeout(300)
        mine = await ev("[...document.querySelectorAll('table.t tbody tr')].map(r=>r.dataset.nav)")
        check("Needs my action (finance): advice on j1/k1 + BuCA c1", sorted(mine) == ["#i-c1", "#i-j1", "#i-k1"], str(mine))
        await p.screenshot(path=OUT + "/v3-2-table.png", full_page=True)
        await p.uncheck("#mineOnly"); await p.wait_for_timeout(200)

        # owner: new idea with outcome and size in one card
        await role("owner"); await p.click("nav.main >> text=New idea"); await p.wait_for_timeout(500)
        nid = await ev("curId()")
        check("new idea opens on step 1", nid != "" and await ev("stepOf(item(curId()))") == 1)
        await p.click("[data-act=submit]"); await p.wait_for_timeout(200)
        check("submit blocked until outcome + size filled", "KPI" in await p.inner_text("#acterr") and "Rough value" in await p.inner_text("#acterr"))
        await p.fill("#f_title", "Chat transcript summaries for agents")
        await p.select_option("#f_demand_source", "NextGen"); await p.select_option("#f_demand_okr", "o3")
        await p.fill("#f_demand_problem", "Agents read long chat histories before they can answer. This takes minutes per contact and answers vary.")
        await p.fill("#f_demand_affected", "Chat agents"); await p.fill("#f_demand_frequency", "About 12,000 chats per month")
        await p.select_option("#f_outcome_kpi", "Average handling time (sec)")
        await p.fill("#f_outcome_baseline", "480"); await p.fill("#f_outcome_baselineSource", "Verint · chat queue")
        await p.fill("#f_outcome_target", "420"); await p.select_option("#f_outcome_targetDate", "2027 Q2")
        await p.fill("#f_outcome_method", "Weekly AHT on the chat queue"); await p.select_option("#f_demand_size", "M")
        await p.wait_for_timeout(200)
        check("gate ticks all", "Everything needed is filled in" in await p.inner_text("#gate"))
        await p.screenshot(path=OUT + "/v3-3-idea-card.png", full_page=True)
        await p.click("[data-act=submit]"); await p.wait_for_timeout(1500)
        check("submitted to triage", await ev(f"item('{nid}').stage") == 2)

        # finance + product lead advise, PO decides
        await role("finance"); await p.wait_for_timeout(300)
        await p.click("[data-act=adviseNo]"); await p.wait_for_timeout(200)
        check("concerns need a note", "note" in (await p.inner_text("#acterr")).lower())
        await p.fill("#reason", "Check the licence cost for the summariser"); await p.click("[data-act=adviseNo]"); await p.wait_for_timeout(300)
        await role("prod"); await p.wait_for_timeout(300); await p.click("[data-act=adviseYes]"); await p.wait_for_timeout(300)
        adv = await ev(f"item('{nid}').overview.advice.map(a=>a.role+':'+a.view)")
        check("two advices stored", adv == ["finance:concern", "prod:support"], str(adv))
        check("advisers no longer 'Your step'", await ev(f"turn(item('{nid}'))") == ["lead"])
        await role("lead"); await p.wait_for_timeout(300)
        t = await p.inner_text("#art-2")
        check("PO sees the advice in the triage decision", "Has concerns" in t and "Supports" in t)
        check("label pre-filled by the quality check", await ev(f"item('{nid}').overview.type") in ("Run", "CI", "Change"))
        await p.select_option("#f_overview_type", "CI"); await p.click("[data-act=accept]"); await p.wait_for_timeout(400)
        check("accepted goes straight to the business case", await ev(f"item('{nid}').stage") == 4 and await ev(f"stepOf(item('{nid}'))") == 3)
        await p.screenshot(path=OUT + "/v3-4-after-triage.png", full_page=True)

        # pipeline drag-bundle at triage (PO)
        await p.goto(U + "#board"); await p.wait_for_timeout(400)
        await p.drag_and_drop('[data-drag="k1"]', '.bc[data-drop="e1"]'); await p.wait_for_timeout(400)
        check("drag k1 onto e1 bundles it", await ev("item('k1').status") == "merged" and "k1" in await ev("item('e1').overview.bundled"))

        # c1: finance approves -> ready for decision
        await role("finance"); await p.goto(U + "#i-c1"); await p.wait_for_timeout(400)
        await p.click("[data-act=approve]"); await p.wait_for_timeout(400)
        check("approved BuCA is ready for decision", await ev("item('c1').stage") == 5 and await ev("stepOf(item('c1'))") == 4)
        check("ready card shown", "READY FOR DECISION" in await p.inner_text("aside"))
        await p.goto(U + "#board"); await p.wait_for_timeout(300)
        col4 = await p.inner_text(".board .col:nth-child(4)")
        check("c1 in the Ready column", "Auto-routing" in col4)

        # history link goes to v3 step
        await p.goto(U + "#i-a1"); await p.wait_for_timeout(400)
        hrefs = await ev("[...document.querySelectorAll('.hist a')].map(a=>a.getAttribute('href'))")
        check("history links point to steps 1-4", all(h.split("-a")[-1] in "1234" for h in hrefs), str(hrefs))
        await p.click(".hist a[href$='-a1']"); await p.wait_for_timeout(600)
        check("history click opens the idea card", await ev("OPEN['a1'].has(1)"))

        # sent-back idea (d1) for owner
        await role("owner"); await p.goto(U + "#i-d1"); await p.wait_for_timeout(400)
        check("d1 sent back: owner sees why", "sent this back" in await p.inner_text("aside"))

        # Dutch
        await p.goto(U + "#board"); await p.wait_for_timeout(300)
        await p.click('[data-lang="nl"]'); await p.wait_for_timeout(300)
        body = await p.inner_text("body")
        check("Dutch pipeline", "Klaar voor besluit" in body and "Nieuw idee" in body and "Idee + uitkomst" in body)
        check("Dutch role names", "Beoordelaar · PO" in await ev("[...document.querySelectorAll('#roleSel option')].map(o=>o.textContent).join('|')"))
        await p.screenshot(path=OUT + "/v3-5-dutch.png", full_page=True)
        await p.goto(U + "#i-e1"); await p.wait_for_timeout(400)
        check("Dutch triage", "Advies van beoordelaars" in await p.inner_text("#app"))
        check("data unchanged in Dutch", await ev("item('e1').title") == "Self-service move-house flow")
        await p.click('[data-lang="en"]'); await p.wait_for_timeout(300)
        check("back to English", "Advice from reviewers" in await p.inner_text("#app"))

        # phone width
        await p.set_viewport_size({"width": 400, "height": 860}); await p.goto(U + "#board"); await p.wait_for_timeout(300)
        await p.screenshot(path=OUT + "/v3-6-phone.png", full_page=True)

        check("no page errors", not errs, str(errs))
        await b.close()
    print("\n" + ("ALL PASSED" if not fails else f"{len(fails)} FAILED: {fails}"))

asyncio.run(main())
