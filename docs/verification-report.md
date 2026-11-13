# Verification report

## Results

- `npm run build` generated all 35 routes and compiled the production CSS.
- `python tools/verify_site.py` passed: one main landmark and one H1 per route, internal links resolve, local assets exist, and runtime assets do not depend on remote image URLs.
- Browser-tested all 35 routes at 390×844, 768×1024, and 1440×900. No horizontal overflow, missing H1s, or browser console errors were observed.
- Checked keyboard behavior for the mobile menu, desktop dropdowns, education-stage tabs, and search dialog. The mobile menu closes on Escape and restores focus to its trigger; dropdowns and search also close on Escape.
- Checked reduced-motion mode: reveal content stays visible and Motion animations are disabled.
- Checked key CTA color pairs in-browser: primary CTA text is 4.79:1 and the coral closing section is 5.45:1.

## Accessibility scope

Semantic landmarks, skip navigation, image alt text, keyboard-operable controls, visible focus styling, tab semantics, and reduced-motion handling are present. These checks are not a formal WCAG 2.2 AA certification; screen-reader testing and a full contrast audit remain advisable before launch.

## Content and integrations

- Page-to-route coverage and source headings are recorded in [content-inventory.md](content-inventory.md).
- The cached `skills-ai-cant-match` source exposed no readable headings; its redesigned page links back to the official school page rather than inventing copy.
- Inquiry and application submissions remain on the official admissions service. Calendar, portal, downloads, and partner services continue to use their original destinations where exposed by the source.
- The site uses downloaded local school imagery at runtime; external admissions and partner destinations require internet access.
