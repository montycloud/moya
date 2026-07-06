# MOYA website

The public site for MOYA — a hand-crafted static site (plain HTML + CSS + a little
vanilla JS, no build step). Deployed to GitHub Pages.

```
website/
├── index.html        # landing page
├── learn.html        # "Guide" — agentic concepts + first-agent walkthrough
├── assets/
│   ├── styles.css    # the whole design system (CSS variables)
│   ├── main.js       # mobile nav, copy buttons, tiny Python highlighter, TOC scroll-spy
│   ├── moya-mark.svg # logo
│   └── favicon.svg
└── .nojekyll         # serve /assets untouched (no Jekyll processing)
```

## Preview locally

No build needed — just serve the folder:

```bash
python3 -m http.server -d website 8080
# open http://localhost:8080
```

Editing `index.html`, `learn.html`, or the files in `assets/` and refreshing is the whole
loop. All links are **relative**, so the site works both at the domain root and under a
sub-path (GitHub project Pages serve at `/<repo>/`).

## Deploy (GitHub Pages)

Publishing is automated by [`.github/workflows/pages.yml`](../.github/workflows/pages.yml),
which uploads `website/` and deploys it on every push to `main` (or on manual dispatch).

**One-time setup** (repository admin, done once in the GitHub UI):

> **Settings → Pages → Build and deployment → Source: GitHub Actions**

After that:
- Push to `main` (or run the **Deploy website to GitHub Pages** workflow manually via
  *Actions → Run workflow*) and the site publishes automatically.
- The live URL for this repo will be **https://montycloud.github.io/moya/**.

## Design notes

- **Type:** Inter (display + body, up to weight 800) · JetBrains Mono (code), loaded from
  Google Fonts. Technical/product feel, matching the Agent Studio.
- **Palette:** white canvas, navy/slate ink, a single blue accent (`#2563eb`) — matched to
  the Agent Studio. Defined as CSS variables at the top of `styles.css`.
- **No framework, no dependencies.** The Python code samples are highlighted by a ~40-line
  tokenizer in `main.js`; copy buttons and the mobile menu are plain event listeners.
