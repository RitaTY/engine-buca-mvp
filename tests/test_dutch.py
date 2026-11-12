"""EN | NL switch: translation on screen, persistence, switching back, data untouched."""
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
        b = await pw.chromium.launch(); c = await b.new_context(viewport={"width": 1280, "height": 900})
        await c.add_init_script("localStorage.setItem('engine-role', localStorage.getItem('engine-role')||'finance')")
        p = await c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
        await p.goto(U + "#home"); await p.wait_for_timeout(2000)
        check("starts in English", "From demand to decision" in await p.inner_text("h1"))
        await p.click('[data-lang="nl"]'); await p.wait_for_timeout(300)
        check("Dutch home title", "Van vraag naar besluit" in await p.inner_text("h1"))
        check("Dutch navigation", "Besluitagenda" in await p.inner_text("nav.main"))
        check("html lang is nl", await p.evaluate("document.documentElement.lang") == "nl")
        await p.screenshot(path=OUT + "/nl1-home.png", full_page=True)
        await p.goto(U + "#i-c1-a4"); await p.wait_for_timeout(600)
        txt = await p.inner_text("#art-4")
        check("Lean BuCA in Dutch", "Batenhefbomen" in txt and "Kostenregels" in txt, txt[:120])
        check("stored data unchanged", await p.evaluate("item('c1').title") == "Auto-routing of heat-pump service calls")
        await p.screenshot(path=OUT + "/nl2-buca.png", full_page=True)
        await p.reload(); await p.wait_for_timeout(2000)
        check("choice survives a reload", "Batenhefbomen" in await p.inner_text("#app"))
        await p.click('[data-lang="en"]'); await p.wait_for_timeout(300)
        t = await p.inner_text("body")
        check("switching back restores English", "Benefit levers" in t and "Batenhefbomen" not in t and "Viewing as" in t)
        await p.click('[data-lang="nl"]'); await p.goto(U + "#welcome"); await p.wait_for_timeout(400)
        check("role page in Dutch", "Welke rol" in await p.inner_text("h1") or "Kies een rol" in await p.inner_text("h1"))
        await p.click('.rolecard[data-r="owner"]'); await p.wait_for_timeout(400)
        toast = await p.inner_text("#toast")
        check("toast in Dutch", toast.startswith("Je bent nu"), toast)
        check("no page errors", not errs, str(errs))
        await b.close()
    print("\n" + ("ALL PASSED" if not fails else f"{len(fails)} FAILED: {fails}"))
asyncio.run(main())
