import os
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);OUT=os.path.join(HERE,"screenshots");os.makedirs(OUT,exist_ok=True)
import asyncio, subprocess, time
from playwright.async_api import async_playwright

srv = subprocess.Popen(["python3", "-m", "http.server", "8765", "-d", ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.8)
URL = "http://localhost:8765/index.html"
STUB = open(HERE+"/fake-db.js").read()
errs = []

async def page(ctx, name):
    p = await ctx.new_page()
    await p.add_init_script(STUB)
    p.on("pageerror", lambda e: errs.append(name + ": " + str(e)))
    return p

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        A = await page(ctx, "A")
        await A.goto(URL); await A.wait_for_timeout(600)
        print("A empty state:", await A.inner_text("h1"))
        await A.click("#resetBtn2"); await A.click("#resetBtn2"); await A.wait_for_timeout(1200)
        print("A after load:", await A.inner_text("h1"))
        B = await page(ctx, "B")
        await B.goto(URL + "#i-a1"); await B.wait_for_timeout(600)
        print("B sees:", await B.inner_text(".hero h1"))

        # A: triage on the pipeline, drag as PO (lead)
        await A.select_option("#roleSel", "lead")
        await A.goto(URL + "#board"); await A.wait_for_timeout(400)
        await A.screenshot(path=OUT+"/s1-pipeline.png", full_page=True)
        await A.drag_and_drop('[data-drag="k1"]', '.bc[data-drop="e1"]')
        await A.wait_for_timeout(900)
        await A.screenshot(path=OUT+"/s2-after-drag.png", full_page=True)
        print("e1 bundled (A):", await A.evaluate("item('e1').overview.bundled"))
        await B.wait_for_timeout(600)
        print("e1 bundled (B, live):", await B.evaluate("item('e1').overview.bundled"))
        # unbundle k1 from the triage decision on e1
        await A.goto(URL + "#i-e1-a2"); await A.wait_for_timeout(500)
        await A.click('[data-act=unbundle][data-s="k1"]'); await A.wait_for_timeout(500)
        print("k1 status after unbundle:", await A.evaluate("item('k1').status"))

        # B: finance returns c1, owner adds levers
        await B.select_option("#roleSel", "finance")
        await B.goto(URL + "#i-c1"); await B.wait_for_timeout(400)
        await B.fill("#reason", "Please split routing and FCR benefits")
        await B.click("[data-act=returnBuca]"); await B.wait_for_timeout(500)
        await B.select_option("#roleSel", "owner"); await B.wait_for_timeout(300)
        before = await B.evaluate("calc(item('c1')).annual")
        await B.drag_and_drop('.lchip[data-lever="repeat"]', '[data-leverdrop]', target_position={'x':60,'y':20})
        await B.wait_for_timeout(400)
        n = await B.evaluate("item('c1').buca.levers.length")
        print('after drag', n, await B.evaluate("JSON.stringify(item('c1').buca.levers)"), await B.evaluate("item('c1').buca.fin"), await B.locator('[data-leverdrop]').count(), await B.locator('.lchip').count())
        await B.fill("#f_buca_levers_2_vol", "4000"); await B.fill("#f_buca_levers_2_rep", "20"); await B.fill("#f_buca_levers_2_red", "30")
        await B.click('.lchip[data-lever="manual"]'); await B.fill("#f_buca_levers_3_hpw", "6")
        await B.wait_for_timeout(900)
        after = await B.evaluate("calc(item('c1')).annual")
        print("levers:", n, "->", await B.evaluate("item('c1').buca.levers.length"), "annual", round(before), "->", round(after))
        print("lv-2 label:", await B.inner_text("#lv-2"))
        await B.screenshot(path=OUT+"/s3-levers.png", full_page=True)
        await B.click('[data-act=rmLever][data-k="3"]'); await B.wait_for_timeout(300)
        await B.click("[data-act=toFinance]"); await B.wait_for_timeout(900)
        await A.wait_for_timeout(500)
        print("A sees c1 fin:", await A.evaluate("item('c1').buca.fin"), "levers", await A.evaluate("item('c1').buca.levers.length"))
        await A.goto(URL + "#i-c1"); await A.wait_for_timeout(400)
        hist = await A.inner_text(".tl")
        print("history names:", hist.splitlines()[:2])
        # mobile triage
        await A.set_viewport_size({"width": 400, "height": 860})
        await A.goto(URL + "#board"); await A.wait_for_timeout(300)
        await A.screenshot(path=OUT+"/s4-mobile.png")
        await b.close()
        # local mode
        b = await pw.chromium.launch(); p = await b.new_page()
        p.on("pageerror", lambda e: errs.append("L: " + str(e)))
        await p.goto(URL); await p.wait_for_timeout(2200)
        print("local:", await p.inner_text("#annText"), "|", await p.inner_text("h1"))
        await b.close()
    print("errors:", errs)

asyncio.run(main())
srv.terminate()
