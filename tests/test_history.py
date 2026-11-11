import os
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);OUT=os.path.join(HERE,"screenshots");os.makedirs(OUT,exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
U="file://"+ROOT+"/index.html"
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch();p=await b.new_page(viewport={"width":1280,"height":900});errs=[];p.on("pageerror",lambda e:errs.append(str(e)))
        await p.goto(U+"#i-h1");await p.wait_for_timeout(2000)
        await p.screenshot(path=OUT+"/h1.png")
        links=await p.eval_on_selector_all(".hist a","els=>els.map(e=>e.getAttribute('href')+' '+e.querySelector('.hart').textContent)");print(links)
        await p.click(".hist a[href$='-a7']");await p.wait_for_timeout(900)
        print("hash",await p.evaluate("location.hash"),"open7",await p.evaluate("document.getElementById('art-7').classList.contains('open')"),"flash",await p.evaluate("document.getElementById('art-7').classList.contains('flash')"),"top",await p.evaluate("Math.round(document.getElementById('art-7').getBoundingClientRect().top)"))
        await p.screenshot(path=OUT+"/h2.png")
        # same link again -> still focuses
        await p.evaluate("window.scrollTo(0,0)");await p.click(".hist a[href$='-a7']");await p.wait_for_timeout(900)
        print("refocus top",await p.evaluate("Math.round(document.getElementById('art-7').getBoundingClientRect().top)"))
        # direct deep link load
        p2=await b.new_page(viewport={"width":1280,"height":900});await p2.goto(U+"#i-a1-a4");await p2.wait_for_timeout(2200)
        print("deep link open4",await p2.evaluate("document.getElementById('art-4').classList.contains('open')"),"top",await p2.evaluate("Math.round(document.getElementById('art-4').getBoundingClientRect().top)"))
        # switch role button then new log art
        await p2.click("[data-act=asRole]");await p2.wait_for_timeout(200);print("role",await p2.evaluate("S.role"))
        await p2.fill("#reason","Clear failure-demand win");await p2.click("[data-act=fund]");await p2.wait_for_timeout(300)
        print("last log",await p2.evaluate("JSON.stringify(item('a1').log.slice(-1)[0])"))
        await p2.goto(U+"#i-c1");await p2.wait_for_timeout(300);await p2.screenshot(path=OUT+"/h3.png")
        print(errs);await b.close()
asyncio.run(main())
