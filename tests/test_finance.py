"""Business Control journey: parameter library, photo moment, recalculation,
versions with comparison, logged overrides, cost lines and CAPEX/OPEX checks."""
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
        await p.goto(U); await p.wait_for_timeout(2000)
        ev = p.evaluate
        role = lambda r: p.select_option("#roleSel", r)

        a1_before = await ev("Math.round(calc(item('a1')).annual)")
        c1_before = await ev("Math.round(calc(item('c1')).annual)")
        check("seed: approved a1 has photo and 2 versions", await ev("!!item('a1').buca.photo && item('a1').buca.versions.length===2"))
        check("seed: pending c1 has v1", await ev("item('c1').buca.versions.length===1"))

        # 1. Business Control changes cost per contact
        await role("finance"); await p.goto(U + "#rules"); await p.wait_for_timeout(300)
        await p.select_option("#pSel", "contactCost"); await p.fill("#pVal", "7.2")
        await p.click("[data-act=paramChange]"); await p.wait_for_timeout(200)
        check("param change needs a reason", "reason" in (await p.inner_text("#perr")).lower())
        await p.fill("#pWhy", "New contact cost from the 2027 budget"); await p.click("[data-act=paramChange]"); await p.wait_for_timeout(300)
        check("param history grew", await ev("S.params.contactCost.length===3"))
        check("current cost per contact is 7.2", await ev("S.rules.contactCost===7.2"))
        await p.screenshot(path=OUT + "/f1-parameters.png", full_page=True)
        a1_after = await ev("Math.round(calc(item('a1')).annual)")
        c1_after = await ev("Math.round(calc(item('c1')).annual)")
        check("approved a1 stays frozen", a1_before == a1_after, f"{a1_before} -> {a1_after}")
        check("pending c1 uses the new value", c1_after != c1_before, f"{c1_before} -> {c1_after}")

        # 2. Recalculate a1 with today's parameters
        await p.goto(U + "#i-a1-a4"); await p.wait_for_timeout(500)
        check("drift shown on a1", "Changed since then" in await p.inner_text("#art-4"))
        await p.click("[data-act=recalc]"); await p.wait_for_timeout(200)
        check("recalc needs a reason", "reason" in (await p.inner_text("#recalcerr")).lower())
        await p.fill("#recalcWhy", "Align with the 2027 budget before the decision meeting"); await p.click("[data-act=recalc]"); await p.wait_for_timeout(400)
        check("a1 recalculated: v3 and new value", await ev("item('a1').buca.versions.length===3") and await ev("Math.round(calc(item('a1')).annual)") != a1_before)
        check("recalc logged in change log", await ev("item('a1').buca.changes.some(c=>c.kind==='recalc')"))

        # 3. Return c1, owner adds a cost line and resends with a note
        await p.goto(U + "#i-c1"); await p.wait_for_timeout(400)
        await p.fill("#reason", "Please add the support FTE"); await p.click("[data-act=returnBuca]"); await p.wait_for_timeout(300)
        check("return creates v2", await ev("item('c1').buca.versions.length===2"))
        await role("owner"); await p.wait_for_timeout(300)
        await p.click("[data-act=addCost]"); await p.wait_for_timeout(200)
        await p.select_option("#f_buca_costs_2_type", "fte"); await p.wait_for_timeout(200)
        await p.fill("#f_buca_costs_2_desc", "Intent model support")
        await p.fill("#f_buca_costs_2_fte", "0.3")
        await p.select_option("#f_buca_costs_2_cls", "capex"); await p.wait_for_timeout(200)
        await p.click("[data-act=toFinance]"); await p.wait_for_timeout(200)
        check("resend needs 'what changed'", "reason" in (await p.inner_text("#acterr")).lower(), await p.inner_text("#acterr"))
        await p.fill("#reason", "Added 0.3 FTE support for the intent model"); await p.click("[data-act=toFinance]"); await p.wait_for_timeout(400)
        check("resend creates v3 with note", await ev("item('c1').buca.versions.length===3 && /0.3 FTE/.test(item('c1').buca.versions[2].note)"))

        # 4. Business Control overrides and approves
        await role("finance"); await p.wait_for_timeout(300)
        flags = await p.inner_text("#calc")
        check("CAPEX/OPEX check flags recurring CAPEX", "recurring costs are normally OPEX" in flags)
        check("CAPEX/OPEX check flags licence CAPEX", "licences and subscriptions are normally OPEX" in flags)
        await p.select_option("#ovrSel", "p:realisation"); await p.fill("#ovrVal", "60")
        await p.click("[data-act=override]"); await p.wait_for_timeout(200)
        check("override needs a reason", "reason" in (await p.inner_text("#ovrerr")).lower())
        await p.fill("#ovrWhy", "Routing gains are not proven yet"); await p.click("[data-act=override]"); await p.wait_for_timeout(300)
        check("override applied", await ev("item('c1').buca.ovr.realisation===60"))
        await p.select_option("#ovrSel", "a:levers.1.min"); await p.fill("#ovrVal", "1.5"); await p.fill("#ovrWhy", "Pilot showed 1.5 minutes"); await p.click("[data-act=override]"); await p.wait_for_timeout(300)
        chg = await ev("JSON.stringify(item('c1').buca.changes.map(c=>[c.label,c.old,c.new,c.why]))")
        check("both overrides logged with old/new/why", await ev("item('c1').buca.changes.length===2"), chg)
        await p.click("[data-act=approve]"); await p.wait_for_timeout(400)
        check("approve freezes c1 and creates v4", await ev("!!item('c1').buca.photo && item('c1').buca.versions.length===4 && item('c1').stage===5"))
        await p.goto(U + "#i-c1-a4"); await p.wait_for_timeout(500)
        await p.select_option("#cmpA", "1"); await p.wait_for_timeout(300)
        cmp = await p.inner_text("table.cmp")
        check("compare v1 vs v4 shows the cost line, the override and the result", "Cost line 3" in cmp and "Override" in cmp and "Benefit per year" in cmp, cmp[:300].replace("\n", " | "))
        await p.screenshot(path=OUT + "/f2-buca-finance.png", full_page=True)
        hist = await p.inner_text(".hist")
        check("history has the override", "Override:" in hist)
        print("errors:", errs); check("no page errors", not errs)
        await b.close()
    print("\n" + ("ALL PASSED" if not fails else f"{len(fails)} FAILED: {fails}"))

asyncio.run(main())
