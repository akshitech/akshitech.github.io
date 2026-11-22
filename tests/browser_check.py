#!/usr/bin/env python3
"""Opens every page of the built site in Chromium and fails on:

- any axe violation (WCAG 2.2 AA and best practice), light and dark, at 1440, 390 and 320 px
- sideways scrolling at any of those widths
- a keyboard focus stop without a visible outline
- a phone menu that does not open, close on Escape and return focus

Usage: python tests/browser_check.py BASE_URL AXE_JS

Runs Playwright's own Chromium, the build pinned by the Playwright version, so
every machine and CI test the same engine (`playwright install chromium` once).
Set CHROME to a Chrome or Chromium binary to test that one instead.
"""
import os
import sys
from playwright.sync_api import sync_playwright

base, axe = sys.argv[1].rstrip("/"), sys.argv[2]
paths = ["/", "/products/", "/services/", "/how-it-works/", "/contact/", "/privacy/", "/terms/", "/404.html"]
rules = {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa", "best-practice"]}
fails = []

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None)
    for scheme in ["light", "dark"]:
        for w in [1440, 390, 320]:
            pg = b.new_page(viewport={"width": w, "height": 900}, color_scheme=scheme)
            for path in paths:
                resp = pg.goto(base + path, wait_until="networkidle")
                if resp and resp.status == 404 and path == "/terms/":
                    continue  # the terms draft is unpublished until reviewed
                sw = pg.evaluate("document.documentElement.scrollWidth")
                if sw > w:
                    fails.append(f"{path} {w}px {scheme}: scrolls sideways ({sw}px)")
                pg.add_script_tag(path=axe)
                r = pg.evaluate("rules => axe.run(document, {runOnly: rules})", rules)
                for v in r["violations"]:
                    fails.append(f"{path} {w}px {scheme}: axe {v['id']} on {v['nodes'][0]['target']}")
            pg.close()

    pg = b.new_page(viewport={"width": 1440, "height": 900})
    for path in paths:
        resp = pg.goto(base + path, wait_until="networkidle")
        if resp and resp.status == 404 and path == "/terms/":
            continue
        seen = set()
        for _ in range(100):
            pg.keyboard.press("Tab")
            el = pg.evaluate("""() => { const e = document.activeElement;
                if (!e || e === document.body) return null;
                const s = getComputedStyle(e);
                return {k: e.outerHTML.slice(0, 80), style: s.outlineStyle, width: s.outlineWidth}; }""")
            if not el or el["k"] in seen:
                break
            seen.add(el["k"])
            if el["style"] == "none" or el["width"] == "0px":
                fails.append(f"{path}: focus not visible on {el['k']}")
    pg.close()

    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto(base + "/services/", wait_until="networkidle")
    pg.click(".menu-btn")
    if pg.get_attribute(".menu-btn", "aria-expanded") != "true" or not pg.is_visible("#menu"):
        fails.append("phone menu does not open")
    pg.keyboard.press("Escape")
    if pg.get_attribute(".menu-btn", "aria-expanded") != "false" or pg.is_visible("#menu"):
        fails.append("phone menu does not close on Escape")
    if "menu-btn" not in (pg.evaluate("document.activeElement.className") or ""):
        fails.append("focus does not return to the menu button")

    def bg(pg):
        return pg.evaluate("getComputedStyle(document.body).backgroundColor")
    ref = {}
    for scheme in ["light", "dark"]:
        pg = b.new_page(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
        pg.goto(base + "/", wait_until="networkidle")
        ref[scheme] = bg(pg)
        pg.close()
    if ref["light"] == ref["dark"]:
        fails.append("theme: light and dark backgrounds are the same")
    for system, choice in [("light", "dark"), ("dark", "light")]:
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme=system)
        pg = ctx.new_page()
        pg.goto(base + "/", wait_until="networkidle")
        if not pg.is_visible(".theme-switch"):
            fails.append("theme: footer switch is not visible")
            ctx.close()
            continue
        pg.click(f'.theme-switch [data-theme-choice="{choice}"]')
        if bg(pg) != ref[choice]:
            fails.append(f"theme: choosing {choice} on a {system} system does not apply it")
        pg.goto(base + "/products/", wait_until="networkidle")
        if bg(pg) != ref[choice] or pg.get_attribute(f'.theme-switch [data-theme-choice="{choice}"]', "aria-pressed") != "true":
            fails.append(f"theme: {choice} is not kept on the next page")
        pg.add_script_tag(path=axe)
        r = pg.evaluate("rules => axe.run(document, {runOnly: rules})", rules)
        for v in r["violations"]:
            fails.append(f"/products/ chosen {choice} on {system}: axe {v['id']} on {v['nodes'][0]['target']}")
        pg.click('.theme-switch [data-theme-choice="system"]')
        pg.reload(wait_until="networkidle")
        if bg(pg) != ref[system] or pg.get_attribute("html", "data-theme") is not None:
            fails.append(f"theme: System does not return to the {system} system theme")
        ctx.close()
    b.close()

if fails:
    print("\n".join(fails))
    sys.exit(1)
print(f"ok: {len(paths)} pages, 2 themes, 3 widths, keyboard, phone menu and theme switch")
