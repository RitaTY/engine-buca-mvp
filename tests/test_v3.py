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
        n = await ev("document.querySelectorAll('.cards .bc').length")
        check("default view: all ideas in one grid, no columns", n == 7 and await ev("document.querySelectorAll('.board').length") == 0, str(n))
        await p.select_option("#sortSel", "size"); await p.wait_for_timeout(200)
        sizes = await ev("[...document.querySelectorAll('.cards .bc')].map(c=>item(c.getAttribute('href').slice(3)).demand.size)")
        check("sort by size puts L first", sizes[0] == "L" and sizes == sorted(sizes, key=lambda x: {"L":0,"M":1,"S":2}[x]), str(sizes))
        await p.select_option("#sortSel", "type"); await p.wait_for_timeout(200)
        types = await ev("[...document.querySelectorAll('.cards .bc')].map(c=>item(c.getAttribute('href').slice(3)).overview.type||'-')")
        check("sort by label groups Run/CI/Change", types.index("Change") > max(k for k,t in enumerate(types) if t == "CI"), str(types))
        await p.select_option("#sortSel", "step"); await p.wait_for_timeout(200)
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
        check("approved BuCA moves to the hand-off to Aha!", await ev("item('c1').stage") == 5 and await ev("stepOf(item('c1'))") == 4)
        check("PO is next", await ev("turn(item('c1'))") == ["lead"])
        await role("lead"); await p.wait_for_timeout(300)
        prev = await p.inner_text("#art-4")
        check("Aha! initiative preview has outcome and business case", "Outcome" in prev and "Business case (Lean BuCA)" in prev and "ENG-103" in prev)
        payload = await ev("JSON.parse(ahaJson(item('c1')))")
        check("API payload matches Aha! create-initiative shape", payload["initiative"]["name"].startswith("Auto-routing") and payload["initiative"]["workflow_status"]["name"] == "Not started" and payload["initiative"]["custom_fields"]["engine_id"] == "ENG-103")
        await p.click("aside [data-act=ahaDone]"); await p.wait_for_timeout(200)
        check("Aha! reference required", "reference" in (await p.inner_text("#acterr")).lower())
        await p.fill("#ahaRef", "CS-S-12"); await p.fill("#ahaUrl", "https://eneco.aha.io/initiatives/CS-S-12")
        await p.screenshot(path=OUT + "/v3-8-aha.png", full_page=True)
        await p.click("aside [data-act=ahaDone]"); await p.wait_for_timeout(300)
        check("recorded in Aha!", await ev("item('c1').aha.ref") == "CS-S-12" and await ev("turn(item('c1'))") == [])
        check("card says IN AHA!", "IN AHA!" in await p.inner_text("aside"))
        check("history logs the hand-off", "Created in Aha! as CS-S-12" in await p.inner_text(".hist"))
        await p.goto(U + "#board"); await p.wait_for_timeout(300)
        c1 = await p.inner_text('.cards .bc[href="#i-c1"]')
        check("c1 shows step 4 and its Aha! reference", "4 · Hand-off to Aha!" in c1 and "In Aha! · CS-S-12" in c1, c1)

        # history link goes to v3 step
        await p.goto(U + "#i-a1"); await p.wait_for_timeout(400)
        hrefs = await ev("[...document.querySelectorAll('.hist a')].map(a=>a.getAttribute('href'))")
        check("history links point to steps 1-4", all(h.split("-a")[-1] in "1234" for h in hrefs), str(hrefs))
        await p.click(".hist a[href$='-a1']"); await p.wait_for_timeout(600)
        check("history click opens the idea card", await ev("OPEN['a1'].has(1)"))

        # sent-back idea (d1) for owner
        await role("owner"); await p.goto(U + "#i-d1"); await p.wait_for_timeout(400)
        check("d1 sent back: owner sees why", "sent this back" in await p.inner_text("aside"))

        # buckets: team makes its own, shared, starts unsorted
        await p.set_viewport_size({"width": 1280, "height": 2200})  # avoid scrolling mid-drag
        await p.goto(U + "#buckets"); await p.wait_for_timeout(400)
        check("buckets start empty: everything not sorted yet", await ev("(S.buckets||[]).length") == 0 and "No buckets yet" in await p.inner_text("#app"))
        await p.click("[data-act=addBucket]"); await p.wait_for_timeout(200)
        check("bucket needs a name", await ev("(S.buckets||[]).length") == 0)
        for n in ["Now", "Later"]:
            await p.fill("#newBucket", n); await p.click("[data-act=addBucket]"); await p.wait_for_timeout(250)
        check("two buckets added", await ev("S.buckets.map(b=>b.n)") == ["Now", "Later"])
        bid = await ev("S.buckets[0].id")
        await p.drag_and_drop('[data-bdrag="e1"]', f'[data-bucket="{bid}"]'); await p.wait_for_timeout(300)
        check("drag e1 into Now", await ev("item('e1').bucket") == bid)
        check("bucket doesn't change the step", await ev("item('e1').stage") == 2)
        await p.select_option('[data-bmove="a1"]', await ev("S.buckets[1].id")); await p.wait_for_timeout(300)
        check("move a1 to Later with the dropdown", await ev("item('a1').bucket") == await ev("S.buckets[1].id"))
        await p.fill(f'[data-bname="{bid}"]', "Now (Q1)"); await p.press(f'[data-bname="{bid}"]', "Tab"); await p.wait_for_timeout(300)
        check("rename bucket", await ev("S.buckets[0].n") == "Now (Q1)")
        await p.screenshot(path=OUT + "/v3-7-buckets.png", full_page=True)
        await p.click(f'[data-act=delBucket][data-b="{bid}"]'); await p.wait_for_timeout(300)
        check("remove bucket: its ideas go back to not sorted", await ev("item('e1').bucket") == "" and len(await ev("S.buckets")) == 1)
        await p.set_viewport_size({"width": 1280, "height": 900})

        # Dutch
        await p.goto(U + "#board"); await p.wait_for_timeout(300)
        await p.click('[data-lang="nl"]'); await p.wait_for_timeout(300)
        body = await p.inner_text("body")
        check("Dutch pipeline", "Overdracht naar Aha!" in body and "Nieuw idee" in body and "Alle ideeën" in body and "Sorteer op" in body)
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
