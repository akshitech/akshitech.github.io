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
    # The footer's last row. Wide screens: copyright left, legal links and the toggle right, on one line.
    # Phones: legal links on the first line; the copyright below with the toggle at the right of its line.
    for w in [320, 390, 1440]:
        pg = b.new_page(viewport={"width": w, "height": 900})
        pg.goto(base + "/", wait_until="networkidle")
        m = pg.evaluate("""() => {
            const mid = r => r.top + r.height / 2;
            const t = [...document.querySelectorAll(".theme-toggle svg")].find(e => e.getClientRects().length);
            const l = document.querySelector(".foot-legal-links a");
            const c = document.querySelector(".foot-legal > span");
            const row = document.querySelector(".foot-legal");
            if (!t || !l || !c || !row) return null;
            const tr = t.getBoundingClientRect(), lr = l.getBoundingClientRect(), cr = c.getBoundingClientRect(), rr = row.getBoundingClientRect();
            return {right: rr.right - tr.right, linkLine: mid(tr) - mid(lr), copyLine: mid(tr) - mid(cr),
                    linkLeft: lr.left - rr.left, copyLeft: cr.left - rr.left, linksAbove: cr.top - lr.bottom,
                    sw: document.documentElement.scrollWidth}; }""")
        if m is None:
            fails.append(f"footer: legal row, a legal link, copyright or theme toggle missing at {w}px")
            pg.close()
            continue
        if abs(m["right"]) > 4:
            fails.append(f"footer: theme toggle is {m['right']:.0f}px from the right edge at {w}px")
        if abs(m["copyLine"]) > 3:
            fails.append(f"footer: theme toggle is not on the copyright line at {w}px")
        if w > 832:
            if abs(m["linkLine"]) > 3:
                fails.append(f"footer: legal links are not on the copyright line at {w}px")
        elif abs(m["linkLeft"]) > 1 or abs(m["copyLeft"]) > 1 or m["linksAbove"] < 0:
            fails.append(f"footer: on phones the links should sit above, and the copyright start its line, at {w}px")
        if m["sw"] > w:
            fails.append(f"footer: page scrolls sideways at {w}px")
        pg.close()
    for system, other in [("light", "dark"), ("dark", "light")]:
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme=system)
        pg = ctx.new_page()
        pg.goto(base + "/", wait_until="networkidle")
        if not pg.is_visible(".theme-toggle"):
            fails.append("theme: footer toggle is not visible")
            ctx.close()
            continue
        def pressed():
            return pg.get_attribute(".theme-toggle", "aria-pressed")
        def settle(js):
            try:
                pg.wait_for_function(js, timeout=3000)
            except Exception:
                pass  # the assertion that follows reports the failure
        def icon_ok(theme):
            return pg.is_visible(".theme-toggle .icon-moon") == (theme == "dark") and pg.is_visible(".theme-toggle .icon-sun") == (theme == "light")
        if pressed() != ("true" if system == "dark" else "false") or not icon_ok(system):
            fails.append(f"theme: toggle does not show the {system} system theme")
        pg.click(".theme-toggle")
        if bg(pg) != ref[other] or pressed() != ("true" if other == "dark" else "false"):
            fails.append(f"theme: toggle on a {system} system does not switch to {other}")
        pg.goto(base + "/products/", wait_until="networkidle")
        if bg(pg) != ref[other] or pg.get_attribute('meta[name="color-scheme"]', "content") != other \
                or pressed() != ("true" if other == "dark" else "false") or not icon_ok(other):
            fails.append(f"theme: {other} is not kept on the next page")
        pg.add_script_tag(path=axe)
        r = pg.evaluate("rules => axe.run(document, {runOnly: rules})", rules)
        for v in r["violations"]:
            fails.append(f"/products/ toggled to {other} on {system}: axe {v['id']} on {v['nodes'][0]['target']}")
        pg.click(".theme-toggle")
        if bg(pg) != ref[system] or pg.get_attribute("html", "data-theme") is not None \
                or pg.get_attribute('meta[name="color-scheme"]', "content") != "light dark" \
                or pressed() != ("true" if system == "dark" else "false") or not icon_ok(system):
            fails.append(f"theme: toggling back does not return to following the {system} system")
        pg.reload(wait_until="networkidle")
        if bg(pg) != ref[system] or pg.get_attribute("html", "data-theme") is not None or pressed() != ("true" if system == "dark" else "false"):
            fails.append(f"theme: after toggling back, a reload does not follow the {system} system")
        # Device follows: with no saved choice the page tracks a device change at once.
        pg.emulate_media(color_scheme=other)
        settle(f"document.querySelector('.theme-toggle').getAttribute('aria-pressed') === '{'true' if other == 'dark' else 'false'}'")
        if bg(pg) != ref[other] or pressed() != ("true" if other == "dark" else "false"):
            fails.append(f"theme: a device change to {other} is not followed")
        pg.emulate_media(color_scheme=system)
        settle(f"document.querySelector('.theme-toggle').getAttribute('aria-pressed') === '{'true' if system == 'dark' else 'false'}'")
        # A saved choice that the device comes to match is dropped, so the site follows the device again.
        pg.click(".theme-toggle")
        pg.emulate_media(color_scheme=other)
        settle("!document.documentElement.hasAttribute('data-theme')")
        if pg.get_attribute("html", "data-theme") is not None or pg.evaluate("localStorage.getItem('theme')") is not None:
            fails.append(f"theme: a saved {other} is kept after the device switched to {other}")
        pg.emulate_media(color_scheme=system)
        settle(f"document.querySelector('.theme-toggle').getAttribute('aria-pressed') === '{'true' if system == 'dark' else 'false'}'")
        if bg(pg) != ref[system]:
            fails.append(f"theme: after the device matched and changed back, the site does not follow it to {system}")
        # A saved choice that already matches the device on load is dropped too.
        pg.evaluate(f"localStorage.setItem('theme', '{system}')")
        pg.reload(wait_until="networkidle")
        if pg.evaluate("localStorage.getItem('theme')") is not None or pg.get_attribute("html", "data-theme") is not None:
            fails.append(f"theme: a saved {system} matching the device is kept on load")
        ctx.close()
    b.close()

if fails:
    print("\n".join(fails))
    sys.exit(1)
print(f"ok: {len(paths)} pages, 2 themes, 3 widths, keyboard, phone menu and theme toggle")
