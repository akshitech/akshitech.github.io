# akshi.tech

The website of Akshi Tech Private Limited: AI agents do the paperwork behind a professional firm's deadlines, and a qualified professional at the firm checks and signs every piece.

Built with Jekyll and deployed to GitHub Pages by `.github/workflows/pages.yml` on every push to `main`.

## Layout

| Path | What it is |
| --- | --- |
| `index.html`, `products.html`, `services.html`, `how-it-works.html`, `contact.html`, `privacy.html`, `terms.html`, `404.html` | The pages; each sets its title, description and URL in front matter |
| `_layouts/default.html` | The one page shell |
| `_includes/` | Head, header, footer, the workflow grid, the link arrow and the workflow count |
| `_data/contact.yml` | Company name, email, phone, WhatsApp, CIN and registered office |
| `_data/nav.yml` | The main and footer navigation |
| `_data/workflows.yml` | The workflows on the Products page; every count on the site comes from here |
| `_sass/`, `assets/css/main.scss` | The stylesheet, split by component; tokens in `_sass/_tokens.scss` mirror the design system |
| `assets/` | Fonts, logo and the phone-menu script |
| `tests/` | Checks run in CI on the built site |
| `CNAME` | The custom domain, akshi.tech |

## Run it

Requires Ruby (version in `.ruby-version`) and Bundler.

```sh
bundle install
bundle exec jekyll serve
```

Then open http://127.0.0.1:4000.

## Checks

CI runs these on every push and pull request; run them before pushing:

```sh
JEKYLL_ENV=production bundle exec jekyll build
python3 tests/check_built.py
bundle exec htmlproofer _site --disable-external
uv run --with playwright==1.55.0 playwright install chromium   # once per machine
python3 -m http.server 8390 -d _site &   # then, with axe-core 4.10.3 saved locally:
uv run --with playwright==1.55.0 python tests/browser_check.py http://127.0.0.1:8390 axe.min.js
```

`check_built.py` checks titles, descriptions, canonical URLs, the current-page link, workflow counts against the data file, and plain ASCII sources. `browser_check.py` uses Playwright's pinned Chromium on any OS (set `CHROME` to test another binary). It runs axe (WCAG 2.2 AA and best practice) in light and dark at 1440, 390 and 320 px, and checks for sideways scrolling, visible keyboard focus and the phone menu.

## Editing

- Company details change in `_data/contact.yml`; a CIN set there appears in the footer.
- Add or remove a workflow in `_data/workflows.yml`; counts on every page follow.
- Pages state products and workflows without "coming soon" or status labels.
- Illustrations in the hero cards say they are illustrative and use no client data.
- The privacy policy is published. The terms of use are a draft under legal review: `published: false` keeps them out of production builds, and the footer links each legal page only once it is built (the preview runs `jekyll serve --unpublished` to show the draft). Each open point is a `TO CONFIRM` marker, and `tests/check_built.py` fails while any remains. To publish the terms: resolve every marker and set `published: true`.
- The footer's theme switch (System, Light, Dark) saves Light or Dark in the browser's localStorage; the inline script in `_includes/head.html` applies it before the page paints, and `_sass/_tokens.scss` holds the dark tokens once, in a mixin used for both the system setting and the saved choice.
- Fonts are separate woff2 files in `assets/fonts/`; the Latin sets are preloaded in `_includes/head.html`.

## Share image

`og-image.png` (1200x630) is rendered from `design/og-image.html`, which uses the built stylesheet. When the home headline changes, edit that file to match, build, and render it with light mode forced so the logo keeps its dark ink. Set `CHROME` to a Chrome or Chromium binary:

```sh
bundle exec jekyll build
"$CHROME" --headless=new --user-data-dir="$(mktemp -d)" \
  --hide-scrollbars --force-device-scale-factor=1 --blink-settings=preferredColorScheme=1 \
  --window-size=1200,630 --screenshot="$PWD/og-image.png" "file://$PWD/design/og-image.html"
```

## Fonts

Newsreader and IBM Plex are used under the SIL Open Font License 1.1; the licence texts are in `assets/fonts/`.
