# Website Setup and Run Instructions

## Technologies

- HTML5 — page structure.
- Tailwind CSS and custom CSS — styling and responsive layouts.
- Vanilla JavaScript — menus, search, tabs, and photo controls.
- Motion — animations and micro-interactions.
- Python — HTML page generation, image downloads, and the local preview server.
- pnpm — JavaScript dependency management.

The project does not use React or Next.js. Images, the logo, CSS, JavaScript, and the Motion library are served locally.

## 1. Run the Ready-to-Use Website

Install Python 3, then open a terminal in the project folder:

```powershell
cd C:\Users\shoaib\Desktop\school_website
python -m http.server 4173 --directory dist
```

Open `http://localhost:4173` in your browser. To stop the server, press `Ctrl+C` in the terminal.

If the `python` command is unavailable, try the Windows Python launcher:

```powershell
py -3 -m http.server 4173 --directory dist
```

You do not need Node.js or JavaScript dependencies to preview the existing `dist` website.

## 2. Rebuild After Editing Source Files

Install Python 3, Node.js, and pnpm before rebuilding:

```powershell
pnpm install
python tools/generate_site.py
pnpm run build:css
python tools/verify_site.py
```

Start the preview server if it is not already running, then refresh your browser:

```powershell
python -m http.server 4173 --directory dist
```

## 3. Important Files and Folders

- `tools/generate_site.py` — shared layouts and HTML page generation.
- `src/styles.css` — Tailwind and base styling.
- `src/advanced.css` — advanced visual styling.
- `src/site.js` — menus and basic interactions.
- `src/advanced.js` — Motion animations, search, and educational-stage tabs.
- `assets/images/` — downloaded original images.
- `assets/image-manifest.json` — mappings between original URLs and local image files.
- `dist/` — the ready-to-use website; serve this folder with your web server.

Edit the source files and rebuild rather than editing generated files inside `dist` directly.

## 4. Restore Missing Source Snapshots or Images

Run these commands only if `source-cache` is missing or you want to refresh the original school content. An internet connection is required for the downloads:

```powershell
powershell -ExecutionPolicy Bypass -File tools/fetch-source.ps1
python tools/local_assets.py
python tools/generate_site.py
pnpm run build:css
python tools/verify_site.py
```

The website preview loads its assets locally without a CDN. Opening official admissions services and other external links still requires an internet connection.
