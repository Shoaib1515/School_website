# BISC South Loop website redesign

A static, multi-page redesign built with semantic HTML, compiled Tailwind CSS, and vanilla JavaScript.

## Setup

1. Fetch current public source snapshots: `powershell -ExecutionPolicy Bypass -File tools/fetch-source.ps1`
2. Install dependencies: `pnpm install`
3. Build: `pnpm run build`
4. Preview: `pnpm run preview`, then open `http://localhost:4173`

The bundled pages are generated into `dist/`. Source snapshots in `source-cache/` are intentionally ignored by Git because they are reproducible and remain the publisher's content.

## Verification

- Responsive target widths: 320, 768, 1024, and 1440 pixels.
- Keyboard: skip link, native links/buttons, Escape-close mobile navigation, visible focus states.
- Motion: 200 ms interface transitions and 500 ms viewport reveals, disabled with `prefers-reduced-motion`.
- Forms: inquiry and application submission stays on the official school website; no fake local submission is implemented.
- Content mapping: see `docs/content-inventory.md`.
- Visual references and art direction: see `docs/design-direction.md`.

