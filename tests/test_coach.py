"""Coach on the idea card (built-in questions, and Claude via a stub) and 'Set up buckets for me'."""
import os, asyncio
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "screenshots"); os.makedirs(OUT, exist_ok=True)
U = "file://" + ROOT + "/index.html"
fails = []
def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""))
    if not ok: fails.append(name)

STUB = """window.claude={use:async n=>n==='sample'?{json:async p=>({fields:{'demand.problem':'Customers call to ask where their refund is because the app shows no status.','demand.affected':'B2C customers waiting for a refund','demand.frequency':'about 3,000 calls per month','title':'Refund status in the app','outcome.kpi':'Contacts per 1,000 customers','outcome.baseline':'12','demand.okr':'o1','demand.size':'M'},reply:'Got it, I put that on the card. Where does the 12 come from?'})}:null}"""

async def say(p, text):
    await p.fill("#coachIn", text); await p.press("#coachIn", "Enter"); await p.wait_for_timeout(250)

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        p = await b.new_page(viewport={"width": 1280, "height": 1000})
        errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
        ev = p.evaluate
        await p.goto(U); await p.wait_for_timeout(1200)

        # built-in coach (no Claude on a plain page)
        await p.click("nav.main >> text=New idea"); await p.wait_for_timeout(400)
        await p.click("[data-act=coachOpen]"); await p.wait_for_timeout(300)
        check("coach opens with a greeting", "Tell me about the problem" in await p.inner_text(".coach"))
        await say(p, "Planners copy Verint data into an Excel sheet by hand every morning to advise on staffing. It takes about 1.5 hours per day and mistakes cause understaffing.")
        id_ = await ev("curId()")
        check("problem + short name from the first message", await ev(f"item('{id_}').demand.problem.startsWith('Planners copy')") and await ev(f"item('{id_}').title.length>5"))
        check("coach shows what it put on the card", "Put on the card" in await p.inner_text(".coach"))
        check("next question is who is affected", "Who is affected" in await p.inner_text(".coach"))
        await say(p, "WFM planners and team leads")
        await say(p, "Every day, about 1.5 hours per planner")
        check("short name already set, so it asks the source next", await ev(f"COACH['{id_}'].ask") == "demand.source")
        await p.click(".qr >> text=NextGen"); await p.wait_for_timeout(250)
        await p.click(".qr >> text=Lower cost to serve"); await p.wait_for_timeout(250)
        check("KPI suggestion chip first", (await p.inner_text(".chips .qr >> nth=0")) == "Average handling time (sec)")
        await p.click(".qr >> text=Service level (%)"); await p.wait_for_timeout(250)
        await say(p, "about eighty")
        check("number check", "need a number" in await p.inner_text(".coach"))
        await say(p, "80"); await say(p, "Verint service level report")
        await say(p, "85"); await p.click(".qr >> text=2027 Q2"); await p.wait_for_timeout(250)
        await say(p, "Weekly service level per interval in Verint")
        await say(p, "maybe 40k a year")
        i = await ev(f"JSON.parse(JSON.stringify(item('{id_}')))")
        check("card filled from the chat", i["demand"]["okr"] == "o3" and i["outcome"]["kpi"] == "Service level (%)" and i["outcome"]["baseline"] == 80 and i["outcome"]["target"] == 85 and i["outcome"]["targetDate"] == "2027 Q2" and i["demand"]["size"] == "S", str(i["demand"]) + str(i["outcome"]))
        check("coach says what's next", "Submit for triage" in await p.inner_text(".coach") or "Your step" in await p.inner_text(".coach"))
        check("coach doesn't flood the history", "Coach" not in await p.inner_text(".hist"))
        await p.screenshot(path=OUT + "/c1-coach.png", full_page=True)

        # Claude path via stub
        c2 = await b.new_context(viewport={"width": 1280, "height": 1000}); await c2.add_init_script(STUB)
        q2 = await c2.new_page(); q2.on("pageerror", lambda e: errs.append(str(e)))
        await q2.goto(U); await q2.wait_for_timeout(1500)
        await q2.click("nav.main >> text=New idea"); await q2.wait_for_timeout(400)
        await q2.click("[data-act=coachOpen]"); await q2.wait_for_timeout(500)
        await q2.fill("#coachIn", "People keep calling about refunds, around 3000 a month, because the app shows nothing"); await q2.press("#coachIn", "Enter"); await q2.wait_for_timeout(600)
        nid = await q2.evaluate("curId()")
        it = await q2.evaluate(f"JSON.parse(JSON.stringify(item('{nid}')))")
        check("Claude fills many fields at once", it["title"] == "Refund status in the app" and it["outcome"]["baseline"] == 12 and it["demand"]["size"] == "M" and it["demand"]["okr"] == "o1", str(it["demand"]))
        check("Claude reply shown, labelled", "Where does the 12 come from" in await q2.inner_text(".coach") and "With Claude" in await q2.inner_text(".coach"))
        await c2.close()

        # buckets: empty until the button
        await p.goto(U + "#buckets"); await p.wait_for_timeout(400)
        check("no buckets until asked", await ev("(S.buckets||[]).length") == 0)
        await p.click("[data-act=autoBuckets]"); await p.wait_for_timeout(400)
        check("one bucket per step", await ev("S.buckets.map(b=>b.n)") == ["Idea + outcome", "Triage", "Business case", "Hand-off to Aha!"])
        check("every open idea placed", await ev("S.items.filter(i=>!dead(i)&&!bucketOf(i)).length") == 0)
        check("placed by step", await ev("bucketOf(item('e1'))===S.buckets[1].id && bucketOf(item('a1'))===S.buckets[3].id"))
        await p.screenshot(path=OUT + "/c2-buckets-auto.png", full_page=True)
        await p.click("#clearB"); await p.wait_for_timeout(200)
        check("start over needs a second click", await ev("S.buckets.length") == 4)
        await p.click("#clearB"); await p.wait_for_timeout(300)
        check("start over removes all", await ev("S.buckets.length") == 0 and await ev("S.items.every(i=>!i.bucket)"))

        check("no page errors", not errs, str(errs))
        await b.close()
    print("\n" + ("ALL PASSED" if not fails else f"{len(fails)} FAILED: {fails}"))
asyncio.run(main())
