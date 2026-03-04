import asyncio
from playwright.async_api import async_playwright

URLS = [
    ("https://ledger.giobi.com/portal/05407620961/budget/143", "budget-143-finasi"),
    ("https://ledger.giobi.com/portal/05407620961/budget/133", "budget-133-digitag"),
    ("https://ledger.giobi.com/portal/00000000000/budget/148", "budget-148-laravel"),
]

async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        for url, slug in URLS:
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                status = resp.status if resp else "no response"
                print(f"{slug}: HTTP {status}")
                
                await page.screenshot(path=f"{slug}-full.png", full_page=True)
                
                gantt = await page.query_selector("#gantt-chart")
                if gantt:
                    inner = await gantt.inner_html()
                    bars = inner.count('position:absolute')
                    print(f"  ✅ Gantt: {bars} bars")
                    
                    # Screenshot the gantt card
                    parent = await gantt.evaluate_handle("el => el.closest('.card')")
                    box = await parent.as_element().bounding_box()
                    if box:
                        await page.screenshot(path=f"{slug}-gantt.png", clip={
                            "x": max(0, box["x"]-5), "y": max(0, box["y"]-5),
                            "width": box["width"]+10, "height": box["height"]+10
                        })
                    results.append((slug, status, bars, True))
                else:
                    print(f"  ⚠️ No Gantt")
                    results.append((slug, status, 0, False))
                    
            except Exception as e:
                print(f"{slug}: ERROR - {e}")
                results.append((slug, "error", 0, False))
            finally:
                await page.close()
        
        # Mobile
        print("\n--- Mobile 375px ---")
        page = await browser.new_page(viewport={"width": 375, "height": 812})
        await page.goto(URLS[0][0], wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        await page.screenshot(path="budget-143-mobile.png", full_page=True)
        gantt = await page.query_selector("#gantt-chart")
        if gantt:
            inner = await gantt.inner_html()
            bars = inner.count('position:absolute')
            print(f"✅ Mobile Gantt: {bars} bars")
        else:
            print("⚠️ No Gantt on mobile")
        await page.close()
        
        await browser.close()
    
    print("\n=== SUMMARY ===")
    for slug, status, bars, has_gantt in results:
        emoji = "✅" if has_gantt and bars > 0 else ("⚠️" if status == 200 else "❌")
        print(f"{emoji} {slug}: HTTP {status}, {'Gantt ' + str(bars) + ' bars' if has_gantt else 'No Gantt'}")

asyncio.run(main())
