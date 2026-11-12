"""First-visit role picker: welcome page, picking a role, switching later, deep links not blocked."""
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
        ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        p = await ctx.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
        await p.goto(U); await p.wait_for_timeout(2000)
        check("first visit shows the welcome page", "Which role" in await p.inner_text("h1"))
        check("six role cards", await p.locator(".rolecard").count() == 6)
        waiting = await p.locator('.rolecard[data-r="finance"] .chip').all_inner_texts()
        check("cards show what is waiting", any("waiting" in w for w in waiting), str(waiting))
        await p.screenshot(path=OUT + "/w1-welcome.png", full_page=True)
        await p.click('.rolecard[data-r="finance"]'); await p.wait_for_timeout(400)
        check("picking sets the role", await p.evaluate("S.role") == "finance")
        check("lands on Home", await p.evaluate("location.hash") == "#home" and "From demand to decision" in await p.inner_text("h1"))
        check("header switcher shows the role", await p.input_value("#roleSel") == "finance")
        await p.reload(); await p.wait_for_timeout(2000)
        check("after reload Home, not the welcome page", "From demand to decision" in await p.inner_text("h1"))
        await p.click(".rolehelp"); await p.wait_for_timeout(300)
        check("'All roles' reopens the picker with the current role marked", "Choose a role" in await p.inner_text("h1") and await p.locator(".rolecard.cur").count() == 1)
        await p.click('.rolecard[data-r="heads"]'); await p.wait_for_timeout(300)
        check("switching from the picker works", await p.evaluate("S.role") == "heads")
        # new visitor with a deep link is not blocked
        ctx2 = await b.new_context(viewport={"width": 1280, "height": 900}); q = await ctx2.new_page()
        await q.goto(U + "#i-a1"); await q.wait_for_timeout(2000)
        check("deep link opens directly for a new visitor", "Proactive meter-reading reminders" in await q.inner_text(".hero h1"))
        await q.set_viewport_size({"width": 400, "height": 860}); await q.goto(U + "#welcome"); await q.wait_for_timeout(300)
        await q.screenshot(path=OUT + "/w2-welcome-phone.png")
        check("no page errors", not errs, str(errs))
        await b.close()
    print("\n" + ("ALL PASSED" if not fails else f"{len(fails)} FAILED: {fails}"))

asyncio.run(main())
