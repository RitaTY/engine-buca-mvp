import os
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);OUT=os.path.join(HERE,"screenshots");os.makedirs(OUT,exist_ok=True)
import asyncio, subprocess, time, json
from playwright.async_api import async_playwright
srv = subprocess.Popen(["python3","-m","http.server","8767","-d",ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.6)
URL="http://localhost:8767/index.html";STUB=open(HERE+"/fake-db.js").read();errs=[]
ops=[{"path":k,"data":v} for k,v in json.load(open(ROOT+"/seed/example-data.json"))["documents"].items()]
seed={o["path"]:o["data"] for o in ops}
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch();ctx=await b.new_context(viewport={"width":1280,"height":900})
        await ctx.add_init_script("localStorage.setItem('FAKEDB',"+json.dumps(json.dumps(seed))+");localStorage.setItem('engine-role','lead')")
        A=await ctx.new_page();await A.add_init_script(STUB);A.on("pageerror",lambda e:errs.append(str(e)))
        await A.goto(URL+"#calendar");await A.wait_for_timeout(800)
        print("rows:",await A.locator(".calrow:not(.calhead)").count(),"suggestions:",await A.locator(".relcard").first.locator(".relrow").count())
        for t in await A.locator(".relcard").first.locator(".relrow").all_inner_texts(): print(" -",t.replace("\n"," | ")[:200])
        await A.screenshot(path=OUT+"/c1.png",full_page=True)
        await A.locator('.calrow[data-id="a1"] .caltrack').click();await A.wait_for_timeout(200)
        print("classes:",await A.eval_on_selector_all(".calrow[data-id]","els=>els.map(e=>e.dataset.id+':'+e.className.replace('calrow','').trim())"))
        await A.locator('.calrow[data-id="a1"] .caltrack').click()
        await A.locator('[data-act=relConfirm]').first.click();await A.wait_for_timeout(900)
        print("confirmed in db:",json.loads(await A.evaluate("localStorage.getItem('FAKEDB')"))["cfg/main"].get("links"))
        await A.locator('[data-act=relDismiss]').first.click();await A.wait_for_timeout(500)
        await A.click("#relAI");await A.wait_for_timeout(4800);print("ai err:",await A.inner_text("#relerr"))
        await A.goto(URL+"#i-a1");await A.wait_for_timeout(500)
        print("related card:",(await A.locator("aside").inner_text())[:300].replace("\n"," | "))
        await A.screenshot(path=OUT+"/c2.png")
        # cap lead edits months on g1 -> bar moves
        await A.goto(URL+"#board");await A.wait_for_timeout(300);await A.screenshot(path=OUT+"/c3.png",clip={"x":0,"y":0,"width":1280,"height":500})
        await b.close()
    print("errors",errs)
asyncio.run(main());srv.terminate()
