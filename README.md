# MOVY MSX portal — files included

- `index.html`: a complete lightweight single-tile landing page with remote/keyboard Enter activation. This can be hosted as a normal GitHub Pages site.
- `start.json` and `data/menu.json`: minimal MSX start/menu configuration. **MSX portal JSON schemas vary by MSX setup/version; validate these against your MSX configuration before using them as the MSX start URL.**

## GitHub Pages
1. Create a public repository (e.g. `movy-msx`).
2. Upload the contents of this folder, preserving `data/` and `img/` folders.
3. Repository → Settings → Pages → Deploy from a branch → `main` → `/ (root)` → Save.
4. Open the published `https://YOUR-USERNAME.github.io/movy-msx/` URL on a device to check it.

## Samsung Series 5 compatibility
The page uses plain HTML, CSS, and ES5-style JavaScript, no external libraries, and a large focusable link. Actual support depends on the exact TV model/year and browser. The page only opens `https://www.movy.sx/`; Movy's site and video player must themselves support your TV browser. This cannot be guaranteed without testing on the TV.
