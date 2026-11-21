#!/usr/bin/env python3
"""Checks the built site in _site. Exits non-zero on any failure.

- every page has a unique <title>, a description and an absolute canonical URL
- every page in the main nav, and Contact, marks exactly one main-nav link as current; other pages none
- no "TO CONFIRM" marker is left in a built page (legal drafts awaiting review)
- the workflow count stated anywhere ("N workflows") matches _data/workflows.yml
- source files are plain ASCII (entities like &#8377; are fine)
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_site")
errors = []

pages = []
for d, _, files in os.walk(SITE):
    for f in files:
        if f.endswith(".html"):
            pages.append(os.path.join(d, f))

data = open(os.path.join(ROOT, "_data", "workflows.yml"), encoding="utf-8").read()
total = len(re.findall(r"^\s+- name:", data, re.M))
nav_data = open(os.path.join(ROOT, "_data", "nav.yml"), encoding="utf-8").read()
in_nav = {u.strip("/") for u in re.findall(r"^\s+url:\s*(\S+)", nav_data, re.M)} | {"contact"}

titles = {}
for p in pages:
    rel = os.path.relpath(p, SITE)
    s = open(p, encoding="utf-8").read()
    if 'http-equiv="refresh"' in s:
        continue  # a redirect stub from jekyll-redirect-from, not a page
    t = re.search(r"<title>([^<]+)</title>", s)
    if not t:
        errors.append(f"{rel}: no title")
    else:
        titles.setdefault(t.group(1), []).append(rel)
    if not re.search(r'<meta name="description" content="[^"]+"', s):
        errors.append(f"{rel}: no description")
    if not re.search(r'<link rel="canonical" href="https://', s):
        errors.append(f"{rel}: canonical missing or not absolute")
    nav = re.search(r'<nav aria-label="Main">(.*?)</nav>', s, re.S)
    current = re.findall(r'aria-current="page"', nav.group(1)) if nav else []
    slug = os.path.dirname(rel) if os.path.basename(rel) == "index.html" else rel
    want = 1 if slug in in_nav else 0
    if len(current) != want:
        errors.append(f"{rel}: {len(current)} current links in the main nav, expected {want}")
    if "TO CONFIRM" in s:
        errors.append(f"{rel}: has a TO CONFIRM marker; finish the legal review before deploying")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))
    for n in re.findall(r"(\d+) workflows", text):
        if int(n) != total:
            errors.append(f"{rel}: says {n} workflows, data has {total}")

for t, ps in titles.items():
    if len(ps) > 1:
        errors.append(f"duplicate title {t!r} on {ps}")

skip = {"_site", "vendor", ".git", ".jekyll-cache", "node_modules"}
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if x not in skip]
    for f in files:
        if f.endswith((".html", ".md", ".yml", ".scss", ".js", ".py")):
            path = os.path.join(d, f)
            if os.path.basename(path) == "_fonts.scss":
                continue
            for n, line in enumerate(open(path, encoding="utf-8"), 1):
                if any(ord(c) > 127 for c in line):
                    errors.append(f"{os.path.relpath(path, ROOT)}:{n}: non-ASCII character")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"ok: {len(pages)} pages, {total} workflows")
