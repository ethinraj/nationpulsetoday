# NationPulse Today

Source for https://nationpulsetoday.com — Hinglish news & editorials, published twice daily.

- `content/editions/*.json` — one file per edition (newest becomes the homepage)
- `assets/style.css` — site styles
- `build.py` — generates the static site into `site/` (no dependencies)
- `.github/workflows/pages.yml` — builds and deploys to GitHub Pages on every push

To publish a new edition: add a new JSON file to `content/editions/` and push.
