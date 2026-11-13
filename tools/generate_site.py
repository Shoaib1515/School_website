from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
try:
    from .local_assets import localize_document
except ImportError:
    from local_assets import localize_document

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
        return f'<details class="nav-dropdown group relative"><summary class="nav-link cursor-pointer list-none"{current}>{label}<span aria-hidden="true" class="ml-2 text-sky transition group-open:rotate-180">⌄</span></summary><div class="absolute left-0 top-full z-50 mt-2 min-w-64 border-t-4 border-coral bg-white py-2 shadow-xl">{items}</div></details>'

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
        if kind == "h2" and len(text) < 150:
            if current["content"]:
                groups.append(current)
            current = {"title": text, "content": []}
        elif kind in {"h3", "h4"} and len(text) < 100:
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
        source = BASE + SCHOOL_ROOT + ('/' + page.path if page.path else '')
        return f'<section class="wrap py-16"><a class="text-link" href="{source}">Explore this topic on the official school website ↗</a></section>'
    result = []
    images = page.images[1:] if len(page.images) > 1 else page.images
    for index, group in enumerate(groups):
        section_title = html.escape(group["title"])
        preview_items = group["content"][:1]
        first_text = preview_items[0][1] if preview_items else ""
        preview = short_preview(first_text)
        body = f'<p class="section-preview">{html.escape(preview)}</p>'
        body += f'<details class="read-more"><summary>Read more <span aria-hidden="true">+</span></summary><div class="prose-school">{render_content(group["content"])}</div></details>'
        image_markup = ""
        if images and index < 5:
            src, alt, width, height = images[index % len(images)]
            image_markup = f'<figure class="overflow-hidden bg-cream"><img loading="lazy" src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" width="{width or 900}" height="{height or 650}" class="aspect-[4/3] h-full w-full object-cover transition duration-500 hover:scale-[1.02]"></figure>'
        layout = "lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,.8fr)]" if image_markup else "lg:grid-cols-1"
        result.append(f"""
<section id="section-{index + 1}" class="story-section reveal section-rule py-16 sm:py-20">
  <div class="wrap grid items-start gap-10 {layout}">
    <div><p class="eyebrow">{index + 1:02d}</p><h2 class="mb-7 mt-3 max-w-4xl font-display text-4xl leading-tight text-navy sm:text-5xl">{section_title}</h2><div class="prose-school">{body}</div></div>
    {image_markup}
  </div>
</section>""")
    return "".join(result)


def short_preview(text: str, limit: int = 160) -> str:
    sentence = re.split(r'(?<=[.!?])\s+', text)[0]
    if len(sentence) <= limit:
        return sentence
    return sentence[:limit].rsplit(' ', 1)[0].rstrip(',;:') + '…'


def home_sections(page: SourcePage, title: str, intro: str) -> str:
    stages = [
        ('Early Years', '3–5 years', 'early-years'),
        ('Primary School', '5–11 years', 'primary-school'),
        ('Middle School', '11–14 years', 'middle-school'),
        ('High School', '14–18 years', 'upper-high-school')
    ]
    cards = []
    for index, (label, age, slug) in enumerate(stages):
        stage = parse_page({'path': 'academic-excellence/' + slug, 'name': 'academic-excellence__' + slug})
        photo = stage.images[0] if stage.images else page.images[0]
        cards.append(f'<a class="stage-tile" href="/academic-excellence/{slug}/"><img loading="lazy" width="700" height="900" src="{html.escape(photo[0], quote=True)}" alt="{html.escape(photo[1], quote=True)}"><div class="stage-caption"><span>{age}</span><h3>{label}</h3><span class="stage-arrow" aria-hidden="true">↗</span></div></a>')
    groups = group_blocks(page, title, intro)
    principal = next((text for kind, text in page.blocks if text.startswith('At the heart of our school')), '')
    portrait = next((photo for photo in page.images if 'jimmy' in photo[0].lower()), page.images[0])
    academics = next((group for group in groups if 'NO TWO' in group['title']), {'content': []})
    pillars = next((group for group in groups if 'LEARNING EXPERIENCE' in group['title']), {'content': []})
    science = next((photo for photo in page.images if 'science' in photo[1].lower()), page.images[0])
    return f'''
<section class="stage-section wrap reveal">
  <div class="section-heading"><div><p class="eyebrow">A journey of possibilities</p><h2>A place for every<br><em>stage of discovery.</em></h2></div><a class="text-link" href="/academic-excellence/">Explore our learning journey <span aria-hidden="true">↗</span></a></div>
  <div class="stage-grid">{''.join(cards)}</div>
  <details class="read-more"><summary>About our approach <span aria-hidden="true">+</span></summary><div class="prose-school"><p>{html.escape(intro)}</p></div></details>
</section>
<section class="principal-section reveal"><div class="wrap principal-grid"><figure><img loading="lazy" src="{html.escape(portrait[0], quote=True)}" alt="Jimmy Frawley, Principal" width="600" height="650"></figure><div><p class="eyebrow">A personal welcome</p><span class="quote-mark" aria-hidden="true">“</span><h2>Confidence.<br>Character.<br><em>Curiosity.</em></h2><p class="principal-name">Jimmy Frawley <span>Principal, BISC South Loop</span></p><details class="read-more"><summary>Read the principal’s message <span aria-hidden="true">+</span></summary><div class="prose-school"><p>{html.escape(principal)}</p></div></details></div></div></section>
<section class="academic-section wrap reveal"><div class="academic-copy"><p class="eyebrow">Made for your child</p><h2>No two children<br>learn <em>the same way.</em></h2><p class="section-preview">Personalized learning is at the heart of our education approach.</p><a class="button" href="/academic-excellence/">Discover the difference</a><details class="read-more"><summary>Our academic approach <span aria-hidden="true">+</span></summary><div class="prose-school">{render_content(academics['content'])}</div></details></div><figure><img loading="lazy" width="800" height="900" src="{html.escape(science[0], quote=True)}" alt="{html.escape(science[1], quote=True)}"><figcaption>Academic excellence. Individual ambition.</figcaption></figure></section>
<section class="possibilities-section reveal"><div class="wrap"><p class="eyebrow">Beyond the expected</p><h2>A bigger world.<br><em>A brighter future.</em></h2><div class="experience-links"><a href="/collaborations/">World-class collaborations <span>↗</span></a><a href="/outstanding-experiences/">Extraordinary experiences <span>↗</span></a><a href="/outstanding-experiences/social-purpose/">Purpose beyond the classroom <span>↗</span></a></div><details class="read-more"><summary>Explore our educational pillars <span aria-hidden="true">+</span></summary><div class="prose-school">{render_content(pillars['content'])}</div></details></div></section>
<section class="wrap news-section reveal"><div class="section-heading"><div><p class="eyebrow">Life at South Loop</p><h2>Stories worth <em>sharing.</em></h2></div><a class="text-link" href="/news/">All news <span>↗</span></a></div>{home_news()}</section>
<details class="wrap read-more source-details"><summary>More about BISC South Loop <span aria-hidden="true">+</span></summary><div class="prose-school">{render_content(page.blocks)}</div></details>
'''


def home_news() -> str:
    cards = []
    for name in ['news__hyrox', 'news__open-house', 'news__niche']:
        item = next(item for item in json.loads((ROOT / 'tools/pages.json').read_text()) if item['name'] == name)
        page = parse_page(item)
        title = choose_title(page)
        image = next((photo for photo in page.images if 'author' not in photo[1].lower() and 'default' not in photo[0].lower()), None)
        if name == 'news__hyrox':
            home = parse_page({'path': '', 'name': 'home'})
            image = next((photo for photo in home.images if 'hyrox' in photo[0].lower()), image)
        media = f'<img loading="lazy" width="800" height="500" src="{html.escape(image[0], quote=True)}" alt="{html.escape(image[1], quote=True)}">' if image else ''
        cards.append(f'<a class="news-tile" href="{local_href(page.path)}">{media}<span class="eyebrow">School stories</span><h3>{html.escape(title)}</h3><span class="text-link">Read story ↗</span></a>')
    return '<div class="news-grid">' + ''.join(cards) + '</div>'


def stage_explorer() -> str:
    stages = [('Early Years', '3–5', 'early-years'), ('Primary', '5–11', 'primary-school'),
              ('Middle School', '11–14', 'middle-school'), ('High School', '14–18', 'upper-high-school')]
    tabs, panels = [], []
    for i, (label, age, slug) in enumerate(stages):
        source = parse_page({'path': 'academic-excellence/' + slug, 'name': 'academic-excellence__' + slug})
        photo = source.images[0] if source.images else None
        image = f'<img loading="lazy" width="800" height="650" src="{html.escape(photo[0], quote=True)}" alt="{html.escape(photo[1], quote=True)}">' if photo else ''
        tabs.append(f'<button type="button" role="tab" id="stage-tab-{i}" aria-controls="stage-panel-{i}" aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}">{label}<small>Ages {age}</small></button>')
        panels.append(f'<div role="tabpanel" id="stage-panel-{i}" aria-labelledby="stage-tab-{i}" tabindex="0" {"hidden" if i else ""}><div class="explorer-image">{image}<span class="age-display">{age}<small>YEARS OLD</small></span></div><div class="explorer-copy"><p class="eyebrow">A journey that grows with them</p><h3>{label}.<br><em>Their next chapter.</em></h3><p>{html.escape(short_preview(choose_intro(source, choose_title(source)), 210))}</p><a class="button" href="/academic-excellence/{slug}/">Explore {label}</a></div></div>')
    return '<section class="explorer-section wrap reveal"><div class="section-heading"><div><p class="eyebrow">Find their starting point</p><h2>Small beginnings.<br><em>Extraordinary possibilities.</em></h2></div><span class="section-index">01 / THE JOURNEY</span></div><div data-tabs class="stage-explorer"><div role="tablist" aria-label="Explore educational stages">' + ''.join(tabs) + '</div>' + ''.join(panels) + '</div></section>'


def admissions_journey() -> str:
    steps = [
        ('Inquire', 'Our Director of Admissions will be delighted to share the program with you, and learn about your child and the next steps in their education.', '/admissions/inquiry/', 'Start an inquiry'),
        ('Visit', 'We would like to welcome you to the community, showcasing the state of the art facilities, and introducing you to students and teachers.', '/campus/', 'Explore our campus'),
        ('Apply', 'You’ll need to provide two years of transcripts and Teacher Evaluation Forms.', '/admissions/online-application-form/', 'Apply for a place')
    ]
    items = ''.join(f'<details class="journey-step" {"open" if i == 0 else ""}><summary><span>0{i + 1}</span>{title}<span class="step-plus" aria-hidden="true">+</span></summary><div><p>{text}</p><a class="text-link" href="{href}">{label} ↗</a></div></details>' for i, (title, text, href, label) in enumerate(steps))
    return f'<section class="admissions-feature reveal"><div class="wrap admissions-grid"><div><p class="eyebrow">A new chapter starts here</p><h2>Big futures.<br><em>Simple first steps.</em></h2><p>We personalize our admissions process to you and are here to help at every stage.</p><a class="button" href="/admissions/">Meet admissions</a></div><div class="journey-steps">{items}</div></div></section>'


def related_pages(page: SourcePage) -> str:
    family = page.path.split('/')[0]
    items = json.loads((ROOT / 'tools/pages.json').read_text())
    related = [item for item in items if item['path'] != page.path and item['path'].startswith(family + '/') and '/2026/' not in item['path']]
    if not related:
        related = [item for item in items if item['path'] in ['admissions', 'academic-excellence', 'campus', 'parent-essentials'] and item['path'] != page.path]
    links = ''.join(f'<a href="{local_href(item["path"])}"><span>{i + 1:02d}</span><h3>{html.escape(item["path"].split("/")[-1].replace("-", " ").title())}</h3><span aria-hidden="true">↗</span></a>' for i, item in enumerate(related))
    return f'<section class="wrap related-section reveal"><p class="eyebrow">Keep exploring</p><div class="related-grid">{links}</div></section>'


def search_dialog() -> str:
    items = json.loads((ROOT / 'tools/pages.json').read_text())
    links = []
    for item in items:
        label = 'Home' if not item['path'] else item['path'].split('/')[-1].replace('-', ' ').title()
        if '/2026/' in item['path']:
            label = choose_title(parse_page(item))
        links.append(f'<a data-search-result href="{local_href(item["path"])}"><span>{html.escape(label)}</span><small>{html.escape(item["path"].split("/")[0] or "BISC South Loop")}</small><span aria-hidden="true">↗</span></a>')
    return '<button class="search-launch" data-search-open aria-haspopup="dialog" aria-controls="site-search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><span>Find a page</span><kbd>/</kbd></button><dialog id="site-search" class="search-dialog" aria-labelledby="search-title"><div class="search-heading"><div><p class="eyebrow">Your South Loop guide</p><h2 id="search-title">What would you like to explore?</h2></div><button data-search-close aria-label="Close search">×</button></div><label for="page-search">Search school pages</label><input id="page-search" type="search" placeholder="Try tuition, primary, calendar…" autocomplete="off"><p data-search-status role="status" class="search-status">Browse all school pages</p><div class="search-results">' + ''.join(links) + '</div></dialog>'


def photo_controls(page: SourcePage) -> str:
    candidates = [photo for photo in page.images if 'author' not in photo[1].lower() and 'ai' != photo[1].lower()]
    selected = candidates[:1]
    if not page.path:
        for slug in ['primary-school', 'middle-school']:
            stage = parse_page({'path': 'academic-excellence/' + slug, 'name': 'academic-excellence__' + slug})
            if stage.images:
                selected.append(stage.images[0])
    for token in ['science', 'curriculum', 'facilities']:
        if len(selected) >= 3:
            break
        match = next((photo for photo in candidates if token in photo[1].lower() and photo not in selected), None)
        if match:
            selected.append(match)
    if len(selected) < 2:
        return ''
    return '<div class="photo-controls" role="group" aria-label="School photography">' + ''.join(f'<button data-photo-src="{html.escape(photo[0], quote=True)}" data-photo-alt="{html.escape(photo[1], quote=True)}" aria-label="Show school photograph {i+1}: {html.escape(photo[1], quote=True)}" aria-pressed="{str(i == 0).lower()}">0{i + 1}</button>' for i, photo in enumerate(selected[:3])) + '</div>'


def secure_form_note(path: str) -> str:
    if path not in {"admissions/inquiry", "admissions/online-application-form"}:
        return ""
    source = f"{BASE}{SCHOOL_ROOT}/{path}"
    label = "Open the official secure inquiry form" if path.endswith("inquiry") else "Open the official application form"
    return f'<aside class="bg-sky py-8"><div class="wrap flex flex-col items-start justify-between gap-5 md:flex-row md:items-center"><p class="max-w-2xl font-display text-2xl text-navy">Form submissions remain on the school’s official admissions service.</p><a class="button" href="{source}">{label}</a></div></aside>'


def footer() -> str:
    return """
<section class="bg-coral py-12 text-ink"><div class="wrap flex flex-col items-start justify-between gap-7 md:flex-row md:items-center"><div><p class="text-sm font-bold uppercase tracking-[.18em]">Your next chapter</p><h2 class="mt-2 max-w-3xl font-display text-4xl">We look forward to welcoming your family.</h2></div><a class="button-outline" href="/admissions/">Start your admissions journey</a></div></section>
<footer class="bg-ink py-14 text-white/75"><div class="wrap grid gap-10 md:grid-cols-3"><div><p class="font-display text-2xl text-white">BISC South Loop</p><p class="mt-4 max-w-sm text-sm leading-6">161 W 9th St, Chicago, IL 60605, United States</p></div><div><p class="text-xs font-bold uppercase tracking-[.18em] text-sky">Quick links</p><div class="mt-4 grid gap-2 text-sm"><a href="/parent-essentials/">Parent essentials</a><a href="/news/">Latest news</a><a href="/faqs/">FAQs</a><a href="/campus/our-school/">Our school</a></div></div><div><p class="text-xs font-bold uppercase tracking-[.18em] text-sky">Information</p><div class="mt-4 grid gap-2 text-sm"><a href="/accessibility/">Accessibility</a><a href="/privacy-policy/">Privacy policy</a><a href="/cookie-policy/">Cookie policy</a><a href="/legal-notice/">Legal notice</a></div></div></div><div class="wrap mt-12 border-t border-white/15 pt-6 text-xs">A redesign prototype using school content and media from the official BISC South Loop website.</div></footer>
"""


def render_page(page: SourcePage) -> str:
    title = choose_title(page)
    intro = choose_intro(page, title)
    if page.path == "":
        intro = "We are committed to helping students, from 3 to 18 years, achieve excellence academically, personally, and socially in an inclusive and vibrant community. Our personalized learning approach means your child will achieve more than they ever imagined possible."
    hero_image = page.images[0][0] if page.images else ""
    page_title = html.escape(title)
    description = html.escape(page.description or intro, quote=True)
    canonical = f"{BASE}{SCHOOL_ROOT}{'/' + page.path if page.path else ''}"
    hero_heading = 'Local heritage.<br><em>Global education.</em>' if not page.path else page_title
    hero_intro = 'A world of opportunity. A school that knows your child.' if not page.path else html.escape(short_preview(intro))
    sections = (stage_explorer() + home_sections(page, title, intro)) if not page.path else (
        f'<details class="wrap read-more"><summary>About this page <span aria-hidden="true">+</span></summary><div class="prose-school"><p>{html.escape(intro)}</p></div></details>'
        + page_sections(page, title, intro)
    )
    if not page.path:
        sections = re.sub(r'<section class="stage-section wrap reveal">.*?</section>', '', sections, count=1, flags=re.S)
        sections = sections.replace('<section class="wrap news-section reveal">', admissions_journey() + '<section class="wrap news-section reveal">')
    else:
        groups = group_blocks(page, title, intro)
        if groups:
            toc = ''.join(f'<a href="#section-{i+1}">{html.escape(short_preview(group["title"], 42))}</a>' for i, group in enumerate(groups))
            sections = '<nav class="page-contents" aria-label="On this page"><span>On this page</span>' + toc + '</nav>' + sections
        if page.path == 'admissions':
            sections = admissions_journey() + sections
        sections += related_pages(page)
    hero_class = 'school-hero cinematic-hero' if not page.path else 'school-hero interior-hero'
    hero_heading = '<span>Local heritage.</span><br><em>Global education.</em>' if not page.path else page_title
    controls = photo_controls(page)
    photo_markup = f'<img class="hero-media" src="{html.escape(hero_image, quote=True)}" alt="{html.escape(page.images[0][1], quote=True)}" width="1440" height="1000" fetchpriority="high">' if hero_image else '<div class="hero-photo-fallback" aria-hidden="true"></div>'
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{page_title} | BISC South Loop</title><meta name="description" content="{description}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="/assets/styles.css"><link rel="stylesheet" href="/assets/advanced.css"></head>
<body><div class="reading-progress" aria-hidden="true"></div>{header(page.path)}{breadcrumbs(page.path, title)}
<main id="main">
  <section class="{hero_class}">
    <div class="hero-copy"><p class="eyebrow">Chicago roots. Limitless horizons.</p><h1>{hero_heading}</h1><p class="hero-intro">{hero_intro}</p><div class="hero-actions"><a class="button" href="/admissions/inquiry/">Find your place</a><a class="hero-secondary" href="/campus/">Explore campus <span aria-hidden="true">↗</span></a></div><div class="hero-footnote"><span>British International School of Chicago</span><span>South Loop · Ages 3–18</span></div></div>
    <figure class="hero-photo">{photo_markup}<figcaption><span>YOUR WORLD<br>STARTS HERE.</span><a href="/admissions/" aria-label="Explore admissions">↗</a></figcaption>{controls}</figure>
  </section>
  {secure_form_note(page.path)}
  {sections}
</main>{footer()}{search_dialog()}<a class="back-top" href="#main" aria-label="Back to top">↑</a><script src="/assets/motion.js" defer></script><script src="/assets/site.js" defer></script><script src="/assets/advanced.js" defer></script></body></html>"""
    return html_doc.replace('A redesign prototype using school content and media from the official BISC South Loop website.', 'British International School of Chicago, South Loop · A Nord Anglia Education school')


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
- Authentic school images are stored in `assets/images/` and served locally from `/assets/images/`; no CDN is used at runtime.
- The virtual tour, downloadable documents, calendars, and partner services remain external links where exposed by the source.
"""
    (docs / "design-direction.md").write_text(design, encoding="utf-8")


def main():
    items = json.loads((ROOT / "tools" / "pages.json").read_text(encoding="utf-8"))
    pages = [parse_page(item) for item in items]
    DIST.mkdir(exist_ok=True)
    (DIST / "assets").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "src" / "site.js", DIST / "assets" / "site.js")
    shutil.copyfile(ROOT / "src" / "advanced.js", DIST / "assets" / "advanced.js")
    shutil.copyfile(ROOT / "src" / "advanced.css", DIST / "assets" / "advanced.css")
    shutil.copyfile(ROOT / "node_modules" / "motion" / "dist" / "motion.js", DIST / "assets" / "motion.js")
    shutil.copyfile(ROOT / "node_modules" / "motion" / "LICENSE.md", DIST / "assets" / "motion-LICENSE.md")
    shutil.copytree(ROOT / "assets" / "images", DIST / "assets" / "images", dirs_exist_ok=True)
    for page in pages:
        destination = DIST if not page.path else DIST / page.path
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(localize_document(render_page(page)), encoding="utf-8")
    write_reports(pages)
    print(f"Generated {len(pages)} pages in {DIST}")


if __name__ == "__main__":
    main()

