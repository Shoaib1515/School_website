"""Download the images used by the generated site, including gallery controls."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "image-manifest.json"
IMAGES = ROOT / "assets" / "images"
RESOURCE_ATTRIBUTES = {"src", "poster", "data-photo-src"}


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in RESOURCE_ATTRIBUTES and value and value.startswith(("https://", "http://", "//")):
                self.urls.add(value)


def read_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def localize_document(document):
    manifest = read_manifest()
    parser = Resources()
    parser.feed(document)
    missing = parser.urls - manifest.keys()
    if missing:
        raise RuntimeError("Missing local images. Run tools/local_assets.py before rebuilding. " + str(len(missing)) + " asset(s) missing.")
    for source in parser.urls:
        from html import escape
        document = document.replace(escape(source, quote=True), manifest[source])
    return document


def download(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.nordangliaeducation.com":
        raise ValueError("Unexpected image host: " + url)
    request = Request(url, headers={"User-Agent": "BISC-local-asset-downloader/1.0"})
    with urlopen(request, timeout=60) as response:
        mime = response.headers.get_content_type()
        extensions = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/svg+xml": ".svg", "image/gif": ".gif", "image/avif": ".avif"}
        if mime not in extensions:
            raise ValueError("Unexpected image content type: " + mime)
        content = response.read()
    if not content:
        raise ValueError("Empty image: " + url)
    name = re.sub(r"[^a-z0-9-]", "-", Path(parsed.path).stem.lower())[:65].strip("-") or "school"
    filename = name + "-" + sha256(url.encode()).hexdigest()[:16] + extensions[mime]
    (IMAGES / filename).write_bytes(content)
    return url, "/assets/images/" + filename


def main():
    manifest = read_manifest()
    urls = set()
    from generate_site import parse_page, render_page
    pages = json.loads((ROOT / "tools" / "pages.json").read_text(encoding="utf-8"))
    for page in pages:
        parser = Resources()
        parser.feed(render_page(parse_page(page)))
        urls.update(parser.urls)
    for page in (ROOT / "dist").rglob("*.html"):
        parser = Resources()
        parser.feed(page.read_text(encoding="utf-8"))
        urls.update(parser.urls)
    pending = [url for url in sorted(urls) if url not in manifest or not (ROOT / "assets" / manifest[url].removeprefix("/assets/")).is_file()]
    IMAGES.mkdir(parents=True, exist_ok=True)
    print(f"Images referenced: {len(urls)}. To download: {len(pending)}.", flush=True)
    failures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download, url): url for url in pending}
        for number, future in enumerate(as_completed(futures), 1):
            try:
                source, local = future.result()
                manifest[source] = local
            except Exception as error:
                failures.append((futures[future], str(error)))
            if number % 20 == 0 or number == len(pending):
                print(f"Processed {number}/{len(pending)}", flush=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        for source, error in failures:
            print(f"FAILED {source}: {error}")
        raise SystemExit(1)
    print(f"Saved {len(manifest)} local image mappings. Rebuild to apply them.")


if __name__ == "__main__":
    main()
