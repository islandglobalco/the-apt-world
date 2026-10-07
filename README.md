# APT · the-apt.world

The apartment search that says no.

A single-page site and working product prototype. Everything is in `index.html`: no build step.

- **Hosting:** GitHub Pages from `main`, custom domain in `CNAME`.
- **Data:** all apartments and figures are sample data, labeled as such on the page.
- **Illustrations:** generated in Midjourney (see `docs/midjourney-prompts.md`) and loaded from Midjourney's image CDN. The page draws its own illustrations if those fail to load.
- **Fonts:** the "New Yorker" display face by Allen R. Walden (freeware) is embedded for headlines and labels; `fonts/` holds the original. Cheltenham Condensed Bold is a licensed ITC face: it is used when installed or when a licensed `fonts/cheltenham-condensed-bold.woff2` is added, with Roboto Serif condensed as the stand-in. Body text is Libre Caslon Text.
