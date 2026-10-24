Act as a senior website designer and front-end developer specializing in premium school websites.

Redesign the complete British International School of Chicago, South Loop website with a modern, distinctive, easy-to-understand interface and refined micro-interactions.

**Source website:**  
https://www.nordangliaeducation.com/bisc-south-loop

### 1. Project goal

Create a polished, production-quality redesign that feels professionally art-directed and specific to this school. Help prospective families understand the school, explore its educational stages, and navigate the admissions process easily.

Redesign the full school website, including its relevant internal pages—not only the homepage.

### 2. Fetch and preserve the original content

Before designing, inspect the live website and its school-specific internal links.

- Build a page inventory covering the homepage, admissions, campus, academics, school stages, beyond-the-classroom content, parent resources, news, contact information, and other existing school pages.
- Fetch all accessible page content, including navigation, headings, paragraphs, statistics, quotations, names, CTA labels, accordion content, modal content, forms, and footer information.
- Preserve the original wording and factual content exactly. Do not summarize, rewrite, invent, or silently remove content.
- Improve understanding through layout, typography, grouping, spacing, and navigation.
- Reuse the school’s existing logo, authentic photography, videos, and relevant brand assets where accessible and permitted.
- Preserve meaningful image descriptions and link destinations.
- Treat external applications, portals, and partner websites as external links rather than recreating those services.
- Record unavailable content or assets explicitly. Never claim to have fetched a page you could not access, and never fill gaps with fabricated school information.

Create a source-to-output checklist mapping every source page and content section to its redesigned location.

### 3. Research outstanding school website design

Before implementation, inspect several excellent school or educational institution websites as visual references.

Briefly identify the references and explain which qualities inform the redesign—for example, editorial typography, clear admissions journeys, authentic photography, mobile navigation, and restrained animation.

Use these references to establish a high standard. Develop an original composition suited to this school; do not copy another institution’s identity or layout.

### 4. Visual direction

Aim for a premium, welcoming, contemporary educational identity.

- Build a coherent palette informed by the existing school branding.
- Use expressive but readable typography, with a clear hierarchy and comfortable paragraph widths.
- Combine generous whitespace, strong photographic compositions, and carefully balanced layouts.
- Create variety through editorial sections, image-and-text compositions, restrained grids, and intentional changes in scale.
- Keep long-form academic and admissions content easy to scan.
- Make key admissions actions prominent without overwhelming the page.
- Maintain consistent headers, navigation, buttons, forms, and footer across all pages.

Avoid generic AI-generated website patterns: excessive rounded cards, arbitrary gradients, glass effects everywhere, decorative blobs, repetitive three-column sections, oversized empty hero areas, emoji icons, and unnecessary visual noise.

Every design choice should serve the school’s identity or help families find information.

### 5. Navigation and page structure

Use the content inventory to build a complete, understandable information architecture.

For the homepage, account for the existing introduction, educational stages, principal’s message, academic approach, educational pillars, admissions journey, news, and closing calls to action.

You may reorganize sections to improve flow, but retain all original content and preserve its context.

Provide:

- Clear desktop navigation with accessible dropdowns where needed.
- A well-designed mobile menu.
- Consistent active-page states.
- Breadcrumbs for deeper pages.
- Clear access to admissions, inquiries, and relevant school resources.
- Working internal routes and meaningful external links.

Do not compress the entire website into one excessively long landing page.

### 6. Micro-motion and animation

Use subtle, purposeful motion that makes the interface feel responsive and carefully crafted.

Include appropriate examples such as:

- Gentle section entrances using opacity and small translations.
- Refined button, link, and navigation hover states.
- Smooth dropdown and mobile-menu transitions.
- Modest image hover effects.
- Accessible accordion expansion.
- Subtle header transitions on scroll.

Keep interface transitions around 150–250 milliseconds and section reveals around 400–600 milliseconds, adjusting where appropriate.

Prefer performant transform and opacity animations. Use Intersection Observer for viewport-triggered effects, and avoid excessive animation libraries.

Respect `prefers-reduced-motion`. Ensure content remains visible if JavaScript fails. Avoid scroll hijacking, intrusive parallax, custom cursors, long intro sequences, and animations that delay reading or interaction.

### 7. Required technology

Use only:

- Semantic HTML5.
- Tailwind CSS.
- Vanilla JavaScript.
- Lightweight JavaScript libraries where clearly justified.

Do not use React, Next.js, Vue, Angular, or another application framework.

Use compiled Tailwind CSS for the production deliverable. Organize the project into clear HTML pages, shared styles, JavaScript modules, and assets. Keep dependencies minimal.

### 8. Accessibility, responsiveness, and functionality

- Design for mobile, tablet, laptop, and large desktop screens.
- Target WCAG 2.2 AA accessibility.
- Provide semantic landmarks, logical headings, keyboard navigation, visible focus states, accessible names, and sufficient contrast.
- Make menus, dialogs, tabs, and accordions work with keyboards and touch.
- Optimize images, reserve their layout dimensions, and lazy-load below-the-fold media.
- Preserve page titles, descriptions, and relevant SEO information.
- Avoid broken links, horizontal overflow, layout shifts, and console errors.

All interactive elements must work. If a form requires an unavailable backend, preserve its existing destination or clearly document the integration requirement. Never display a fake successful submission.

### 9. Deliverables and verification

Deliver the implemented website, not just a design description.

Include:

1. A concise content inventory and visual direction.
2. Complete source files and assets.
3. All in-scope redesigned pages.
4. Working navigation and interactions.
5. Setup and local preview instructions.
6. A content-preservation checklist.
7. A short report covering responsive checks, accessibility checks, link checks, and any unavailable content or integrations.

Verify the rendered pages at representative mobile, tablet, and desktop sizes. Compare the final content against the source inventory.

If the project requires multiple stages, track progress and continue through the complete scope. Do not present a homepage-only implementation as a finished website.

**Success means:** the original school content remains intact, families can understand and navigate the site easily, and the finished experience feels distinctive, modern, authentic, and professionally designed.