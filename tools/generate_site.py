from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "source-cache"
DIST = ROOT / "dist"
BASE = "https://www.nordangliaeducation.com"
SCHOOL_ROOT = "/bisc-south-loop"
KNOWN_PATHS = {item["path"] for item in json.loads((ROOT / "tools" / "pages.json").read_text(encoding="utf-8"))}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


@dataclass
class SourcePage:
    path: str
    name: str
    title: str = ""
    description: str = ""
    blocks: list[tuple[str, str]] = field(default_factory=list)
    images: list[tuple[str, str, int, int]] = field(default_factory=list)


class SourceParser(HTMLParser):
    block_tags = {"h1", "h2", "h3", "h4", "p", "li", "blockquote", "dt", "dd"}
    useful_classes = (
        "content-title", "content-subtitle", "item-title", "item-desc", "quote-content",
        "author-name", "author-title", "statement", "promo-title", "promo-description",
        "accordion-title", "accordion-content", "article-body", "rich-text"
    )

    def __init__(self, page: SourcePage):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.depth = 0
        self.in_main = False
        self.stopped = False
        self.skip = 0
        self.capture: dict | None = None
        self.title_capture = False
        self.title_parts: list[str] = []
        self.started = False

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        attrs = dict(attrs)
        classes = attrs.get("class", "")
        if tag == "title":
            self.title_capture = True
        if tag == "meta" and attrs.get("name") == "description":
            self.page.description = clean(attrs.get("content", ""))
        if tag == "main" and "main-content" in classes:
            self.in_main = True
        if self.in_main and "corporate-footer" in classes:
            self.stopped = True
        if not self.in_main or self.stopped:
            return
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
            return
        if tag == "img":
            self._add_image(attrs)
        selected = tag in self.block_tags or attrs.get("role") == "heading"
        selected = selected or (tag == "div" and self._is_text_container(classes))
        if selected and self.capture is None and self.skip == 0:
            kind = tag if tag in self.block_tags else "h" + attrs.get("aria-level", "3")
            self.capture = {"depth": self.depth, "kind": kind, "parts": []}

    def handle_startendtag(self, tag, attrs):
        attrs = dict(attrs)
        if self.in_main and not self.stopped and tag == "img":
            self._add_image(attrs)

    def handle_endtag(self, tag):
        if tag == "title":
            self.title_capture = False
            if not self.page.title:
                self.page.title = clean("".join(self.title_parts))
        if self.capture and self.capture["depth"] == self.depth:
            text = clean(" ".join(self.capture["parts"]))
            kind = self.capture["kind"]
            if text and self._is_content_start(kind, text):
                self.started = True
            if self.started and text:
                previous = self.page.blocks[-1][1] if self.page.blocks else ""
                if text != previous and not self._is_chrome(text):
                    self.page.blocks.append((kind, text))
            self.capture = None
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
        if tag == "main":
            self.in_main = False
        self.depth -= 1

    def handle_data(self, data):
        if self.title_capture:
            self.title_parts.append(data)
        if self.capture and self.skip == 0:
            self.capture["parts"].append(data)

    def _is_content_start(self, kind: str, text: str) -> bool:
        if self.started:
            return True
        if self.page.path == "":
            return text.lower() == "local heritage. global education."
        return kind == "h1" or text.lower() in {"local heritage. global education."}

    @staticmethod
    def _is_chrome(text: str) -> bool:
        return text.lower() in {"search", "inquire now", "back to top", "scroll", "play"}

    def _is_text_container(self, classes: str) -> bool:
        return any(token in classes for token in self.useful_classes) or any(
            token in classes for token in ("__desc", "-desc", "description", "subtitle", "rich-text")
        )

    def _add_image(self, attrs: dict):
        src = attrs.get("data-src") or attrs.get("src")
        if not src or src.startswith("data:"):
            return
        alt = clean(attrs.get("alt", ""))
        try:
            width = int(attrs.get("width", 0))
            height = int(attrs.get("height", 0))
        except ValueError:
            width = height = 0
        fingerprint = f"{src} {alt}".lower()
        if width and width < 450:
            return
        if any(word in fingerprint for word in ("logo", "icon", "pattern", "weather", "badge")):
            return
        absolute = urljoin(BASE, src)
        if not any(existing[0] == absolute for existing in self.page.images):
            self.page.images.append((absolute, alt or "BISC South Loop school community", width, height))


def parse_page(item: dict) -> SourcePage:
    page = SourcePage(path=item["path"], name=item["name"])
    source = CACHE / f"{page.name}.html"
    if not source.exists():
        return page
    parser = SourceParser(page)
    parser.feed(source.read_text(encoding="utf-8", errors="ignore"))
    return page


def local_href(path: str) -> str:
    return "/" if not path else f"/{path}/"


def active(path: str, section: str) -> str:
    return ' aria-current="page"' if path == section or path.startswith(section + "/") else ""


def desktop_nav(path: str) -> str:
    def dropdown(label: str, section: str, links: list[tuple[str, str]]) -> str:
        current = active(path, section)
        items = "".join(
            f'<a class="block px-5 py-3 text-sm font-bold text-ink transition hover:bg-cream hover:text-lake" href="{local_href(href)}">{text}</a>'
            for text, href in links
        )
        return f'<details class="group relative"><summary class="nav-link cursor-pointer list-none"{current}>{label}<span aria-hidden="true" class="ml-2 text-sky transition group-open:rotate-180">⌄</span></summary><div class="absolute left-0 top-full z-50 mt-2 min-w-64 border-t-4 border-coral bg-white py-2 shadow-xl">{items}</div></details>'

    admissions = dropdown("Admissions", "admissions", [
        ("Admissions overview", "admissions"), ("Entry requirements", "admissions/entry-requirements"),
        ("Tuition fees", "admissions/tuition-fees"), ("Inquiry", "admissions/inquiry")
    ])
    campus = dropdown("Our campus", "campus", [
        ("Campus overview", "campus"), ("Facilities", "campus/facilities"), ("Our school", "campus/our-school")
    ])
    academics = dropdown("Academic excellence", "academic-excellence", [
        ("Academic overview", "academic-excellence"), ("Early Years", "academic-excellence/early-years"),
        ("Primary School", "academic-excellence/primary-school"), ("Middle School", "academic-excellence/middle-school"),
        ("Lower High School", "academic-excellence/lower-high-school"), ("Upper High School", "academic-excellence/upper-high-school")
    ])
    beyond = dropdown("Beyond the classroom", "outstanding-experiences", [
        ("Outstanding experiences", "outstanding-experiences"), ("Collaborations", "collaborations"),
        ("Social purpose", "outstanding-experiences/social-purpose")
    ])
    return f"""
      <nav aria-label="Primary" class="hidden items-center gap-7 lg:flex">
        {admissions}{campus}{academics}{beyond}
        <a class="nav-link" href="/about-us/"{active(path, 'about-us')}>About</a>
      </nav>"""


def header(path: str) -> str:
    logo = BASE + "/bisc-south-loop/-/media/chicago-south-loop/homepage/south-loop-logo.png?h=50&iar=0&w=326&rev=bde42b88c01743458f09c25ed075bada&hash=81A5603CB21103B527F18485A9765939"
    mobile_links = [
        ("Admissions", "admissions"), ("Entry requirements", "admissions/entry-requirements"),
        ("Our campus", "campus"), ("Academic excellence", "academic-excellence"),
        ("Early Years", "academic-excellence/early-years"), ("Primary School", "academic-excellence/primary-school"),
        ("Middle School", "academic-excellence/middle-school"), ("High School", "academic-excellence/upper-high-school"),
        ("Beyond the classroom", "outstanding-experiences"), ("Parent essentials", "parent-essentials"),
        ("News", "news"), ("About our school", "about-us")
    ]
    mobile = "".join(f'<a class="border-b border-white/15 py-3 text-lg font-bold text-white" href="{local_href(href)}">{label}</a>' for label, href in mobile_links)
    return f"""
<a href="#main" class="sr-only z-[60] bg-white p-3 text-ink focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
<header data-header class="sticky top-0 z-50 bg-navy transition-shadow duration-200">
  <div class="wrap flex h-20 items-center justify-between gap-8">
    <a href="/" aria-label="BISC South Loop home"><img src="{html.escape(logo, quote=True)}" width="228" height="35" alt="British International School of Chicago, South Loop" class="h-auto w-56 brightness-0 invert"></a>
    {desktop_nav(path)}
    <div class="hidden items-center gap-4 lg:flex"><a class="text-sm font-bold text-white" href="/parent-essentials/">Parents</a><a class="button" href="/admissions/inquiry/">Inquire</a></div>
    <button data-menu-button class="relative z-50 min-h-11 min-w-11 border border-white/40 text-sm font-bold text-white lg:hidden" aria-expanded="false" aria-controls="mobile-menu">Menu</button>
  </div>
  <nav id="mobile-menu" data-menu class="menu-panel" aria-label="Mobile"><div class="flex flex-col">{mobile}</div><a class="button mt-8 w-full" href="/admissions/inquiry/">Inquire now</a></nav>
</header>"""


def breadcrumbs(path: str, title: str) -> str:
    if not path:
        return ""
    parts = path.split("/")
    links = ['<a class="hover:text-coral" href="/">Home</a>']
    current = []
    for part in parts[:-1]:
        current.append(part)
        intermediate = "/".join(current)
        label = html.escape(part.replace("-", " ").title())
        if intermediate in KNOWN_PATHS:
            links.append(f'<a class="hover:text-coral" href="/{intermediate}/">{label}</a>')
        else:
            links.append(f'<span>{label}</span>')
    links.append(f'<span aria-current="page">{html.escape(title)}</span>')
    return '<nav aria-label="Breadcrumb" class="wrap py-5 text-xs font-bold uppercase tracking-[.12em] text-ink/60">' + '<span aria-hidden="true" class="mx-2">/</span>'.join(links) + '</nav>'


def choose_title(page: SourcePage) -> str:
    if page.path == "":
        return "Local heritage. Global education."
    for kind, text in page.blocks:
        if kind == "h1":
            return text
    raw = page.title.split("|")[0].split("-")[0].strip()
    return raw or page.path.split("/")[-1].replace("-", " ").title()


def choose_intro(page: SourcePage, title: str) -> str:
    seen_title = False
    for kind, text in page.blocks:
        if text == title:
            seen_title = True
            continue
        if (seen_title or page.path == "") and kind in {"p", "h3", "div"} and len(text) > 70:
            return text
    return page.description


def group_blocks(page: SourcePage, title: str, intro: str) -> list[dict]:
    groups: list[dict] = []
    current = {"title": "Explore", "content": []}
    skipped_intro = False
    for kind, text in page.blocks:
        if text == title:
            continue
        if text == intro and not skipped_intro:
            skipped_intro = True
            continue
        if kind == "h2":
            if current["content"]:
                groups.append(current)
            current = {"title": text, "content": []}
        elif kind in {"h3", "h4"}:
            current["content"].append(("subhead", text))
        elif kind == "li":
            current["content"].append(("item", text))
        elif len(text) > 2:
            current["content"].append(("p", text))
    if current["content"]:
        groups.append(current)
    return groups


def render_content(items: list[tuple[str, str]]) -> str:
    output: list[str] = []
    in_list = False
    for kind, text in items:
        escaped = html.escape(text)
        if kind == "item":
            if not in_list:
                output.append('<ul>')
                in_list = True
            output.append(f'<li>{escaped}</li>')
            continue
        if in_list:
            output.append('</ul>')
            in_list = False
        if kind == "subhead":
            output.append(f'<h3 class="mb-3 mt-8 font-display text-2xl text-navy">{escaped}</h3>')
        else:
            output.append(f'<p>{escaped}</p>')
    if in_list:
        output.append('</ul>')
    return "".join(output)


def page_sections(page: SourcePage, title: str, intro: str) -> str:
    groups = group_blocks(page, title, intro)
    if not groups:
        return '<section class="wrap py-16"><p class="prose-school">This source page did not expose readable body content in the fetched HTML.</p></section>'
    result = []
    images = page.images[1:] if len(page.images) > 1 else page.images
    for index, group in enumerate(groups):
        section_title = html.escape(group["title"])
        body = render_content(group["content"])
        image_markup = ""
        if images and index < 5:
            src, alt, width, height = images[index % len(images)]
            image_markup = f'<figure class="overflow-hidden bg-cream"><img loading="lazy" src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" width="{width or 900}" height="{height or 650}" class="aspect-[4/3] h-full w-full object-cover transition duration-500 hover:scale-[1.02]"></figure>'
        layout = "lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,.8fr)]" if image_markup else "lg:grid-cols-1"
        result.append(f"""
<section class="reveal section-rule py-16 sm:py-20">
  <div class="wrap grid items-start gap-10 {layout}">
    <div><p class="eyebrow">{index + 1:02d}</p><h2 class="mb-7 mt-3 max-w-4xl font-display text-4xl leading-tight text-navy sm:text-5xl">{section_title}</h2><div class="prose-school">{body}</div></div>
    {image_markup}
  </div>
</section>""")
    return "".join(result)


def secure_form_note(path: str) -> str:
    if path not in {"admissions/inquiry", "admissions/online-application-form"}:
        return ""
    source = f"{BASE}{SCHOOL_ROOT}/{path}"
    label = "Open the official secure inquiry form" if path.endswith("inquiry") else "Open the official application form"
    return f'<aside class="bg-sky py-8"><div class="wrap flex flex-col items-start justify-between gap-5 md:flex-row md:items-center"><p class="max-w-2xl font-display text-2xl text-navy">Form submissions remain on the school’s official admissions service.</p><a class="button" href="{source}">{label}</a></div></aside>'


def footer() -> str:
    return """
<section class="bg-coral py-12 text-white"><div class="wrap flex flex-col items-start justify-between gap-7 md:flex-row md:items-center"><div><p class="text-sm font-bold uppercase tracking-[.18em]">Your next chapter</p><h2 class="mt-2 max-w-3xl font-display text-4xl">We look forward to welcoming your family.</h2></div><a class="button-outline" href="/admissions/">Start your admissions journey</a></div></section>
<footer class="bg-ink py-14 text-white/75"><div class="wrap grid gap-10 md:grid-cols-3"><div><p class="font-display text-2xl text-white">BISC South Loop</p><p class="mt-4 max-w-sm text-sm leading-6">161 W 9th St, Chicago, IL 60605, United States</p></div><div><p class="text-xs font-bold uppercase tracking-[.18em] text-sky">Quick links</p><div class="mt-4 grid gap-2 text-sm"><a href="/parent-essentials/">Parent essentials</a><a href="/news/">Latest news</a><a href="/faqs/">FAQs</a><a href="/campus/our-school/">Our school</a></div></div><div><p class="text-xs font-bold uppercase tracking-[.18em] text-sky">Information</p><div class="mt-4 grid gap-2 text-sm"><a href="/accessibility/">Accessibility</a><a href="/privacy-policy/">Privacy policy</a><a href="/cookie-policy/">Cookie policy</a><a href="/legal-notice/">Legal notice</a></div></div></div><div class="wrap mt-12 border-t border-white/15 pt-6 text-xs">A redesign prototype using school content and media from the official BISC South Loop website.</div></footer>
"""


def render_page(page: SourcePage) -> str:
    title = choose_title(page)
    intro = choose_intro(page, title)
    if page.path == "":
        intro = "We are committed to helping students, from 3 to 18 years, achieve excellence academically, personally, and socially in an inclusive and vibrant community. Our personalized learning approach means your child will achieve more than they ever imagined possible."
    hero_image = page.images[0][0] if page.images else ""
    hero_style = f' style="background-image:linear-gradient(90deg,rgba(8,42,70,.96) 0%,rgba(8,42,70,.74) 48%,rgba(8,42,70,.16) 100%),url(\'{html.escape(hero_image, quote=True)}\')"' if hero_image else ""
    page_title = html.escape(title)
    description = html.escape(page.description or intro, quote=True)
    canonical = f"{BASE}{SCHOOL_ROOT}{'/' + page.path if page.path else ''}"
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{page_title} | BISC South Loop</title><meta name="description" content="{description}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="/assets/styles.css"><script>document.documentElement.classList.add('js')</script></head>
<body>{header(page.path)}{breadcrumbs(page.path, title)}
<main id="main">
  <section class="relative isolate min-h-[34rem] overflow-hidden bg-navy bg-cover bg-center text-white"{hero_style}>
    <div class="wrap flex min-h-[34rem] items-end py-16 sm:py-20"><div class="max-w-4xl"><p class="mb-5 text-sm font-bold uppercase tracking-[.2em] text-sky">British International School of Chicago, South Loop</p><h1 class="font-display text-5xl leading-[.98] sm:text-7xl lg:text-8xl">{page_title}</h1><p class="mt-7 max-w-2xl text-lg leading-8 text-white/85">{html.escape(intro)}</p><div class="mt-9 flex flex-wrap gap-4"><a class="button" href="/admissions/inquiry/">Inquire now</a><a class="button-outline" href="/campus/">Explore our campus</a></div></div></div>
  </section>
  {secure_form_note(page.path)}
  {page_sections(page, title, intro)}
</main>{footer()}<script src="/assets/site.js" defer></script></body></html>"""
    return html_doc


def write_reports(pages: list[SourcePage]):
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    inventory = [
        "# Content inventory and preservation checklist", "",
        "Generated from public source snapshots. Each source heading is retained in the corresponding redesigned route. External services and downloads remain linked to their original destinations.", "",
        "| Source page | Redesigned location | Status | Preserved sections |", "|---|---|---|---|"
    ]
    for page in pages:
        source = f"{BASE}{SCHOOL_ROOT}{'/' + page.path if page.path else ''}"
        output = local_href(page.path)
        headings = [text for kind, text in page.blocks if kind in {"h1", "h2"}][:8]
        status = "Fetched" if (CACHE / f"{page.name}.html").exists() else "Unavailable"
        section_list = ('; '.join(headings) or 'No readable headings exposed').replace('|', '\\|')
        inventory.append(f"| {source} | `{output}` | {status} | {section_list} |")
    (docs / "content-inventory.md").write_text("\n".join(inventory) + "\n", encoding="utf-8")
    design = """# Visual direction and references

## Direction

The redesign uses BISC South Loop's navy and teal heritage with a warm paper ground and a restrained coral admissions accent. Editorial serif display type contrasts with direct sans-serif body copy. Full-bleed authentic photography, numbered chapters, asymmetric image-and-text layouts, and visible admissions actions create a confident, Chicago-specific school experience without repetitive card grids or decorative effects.

## References

- [Girls Preparatory School](https://www.gps.edu/): strong editorial phrases, confident scale changes, and clear admissions actions.
- [Gordonstoun](https://www.gordonstoun.org.uk/admissions/): a compact, human admissions journey organized around visit, webinar, and contact choices.
- [Collège Alpin Beau Soleil](https://www.beausoleil.ch/admissions): immersive photography paired with concise, highly visible admissions guidance.

These references informed hierarchy, pacing, and task clarity only; the composition, palette, content, and interaction language are original to this redesign.

## Integration notes

- Inquiry and application submissions remain on the official school service; the prototype never displays a fake success state.
- Authentic images are loaded from the school's public media CDN, so local previews need an internet connection.
- The virtual tour, downloadable documents, calendars, and partner services remain external links where exposed by the source.
"""
    (docs / "design-direction.md").write_text(design, encoding="utf-8")


def main():
    items = json.loads((ROOT / "tools" / "pages.json").read_text(encoding="utf-8"))
    pages = [parse_page(item) for item in items]
    DIST.mkdir(exist_ok=True)
    (DIST / "assets").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "src" / "site.js", DIST / "assets" / "site.js")
    for page in pages:
        destination = DIST if not page.path else DIST / page.path
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(render_page(page), encoding="utf-8")
    write_reports(pages)
    print(f"Generated {len(pages)} pages in {DIST}")


if __name__ == "__main__":
    main()

