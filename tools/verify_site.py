from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class PageCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.main = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        elif tag == "main":
            self.main += 1
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def local_target(href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or href.startswith(("#", "mailto:", "tel:")):
        return None
    path = parsed.path
    if not path.startswith("/"):
        return None
    return DIST / path.strip("/") / "index.html" if path != "/" else DIST / "index.html"


def main():
    pages = list(DIST.rglob("index.html"))
    assert len(pages) == 35, f"Expected 35 generated pages, found {len(pages)}"
    broken = []
    for page in pages:
        source = page.read_text(encoding="utf-8")
        assert "Lorem ipsum" not in source
        parser = PageCheck()
        parser.feed(source)
        assert parser.h1 == 1, f"{page}: expected one h1, found {parser.h1}"
        assert parser.main == 1, f"{page}: expected one main landmark, found {parser.main}"
        for href in parser.links:
            target = local_target(href)
            if target is not None and not target.exists():
                broken.append((page.relative_to(DIST), href))
    assert not broken, "Broken internal links:\n" + "\n".join(f"{page}: {href}" for page, href in broken)
    assert (DIST / "assets" / "styles.css").stat().st_size > 1000
    assert (DIST / "assets" / "site.js").stat().st_size > 1000
    print(f"Verified {len(pages)} pages: landmarks, headings, assets, and internal links are valid.")


if __name__ == "__main__":
    main()
