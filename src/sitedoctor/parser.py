"""Pure HTML parsing — turns raw HTML into a structured PageData (no network)."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


@dataclass
class Link:
    href: str
    text: str
    rel: str = ""


@dataclass
class Image:
    src: str
    alt: str | None  # None means the alt attribute was missing entirely


@dataclass
class PageData:
    url: str = ""
    title: str | None = None
    lang: str | None = None
    meta: dict[str, str] = field(default_factory=dict)        # name/property -> content
    canonical: str | None = None
    headings: list[tuple[int, str]] = field(default_factory=list)  # (level, text)
    images: list[Image] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    stylesheet_count: int = 0
    script_count: int = 0
    inline_script_bytes: int = 0
    inline_style_blocks: int = 0
    has_jsonld: bool = False
    word_count: int = 0
    html_bytes: int = 0
    # accessibility helpers
    inputs_without_label: int = 0
    total_inputs: int = 0

    @property
    def h1(self) -> list[str]:
        return [t for lvl, t in self.headings if lvl == 1]


_CAPTURE_TAGS = {"title", "a", "h1", "h2", "h3", "h4", "h5", "h6", "label"}


class _Parser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.data = PageData(url=base_url)
        self._cap_stack: list[dict] = []
        self._in_script = False
        self._in_style = False
        self._label_for: set[str] = set()
        self._label_has_text = False

    # -- helpers -----------------------------------------------------------
    def _attr(self, attrs, key):
        for k, v in attrs:
            if k == key:
                return v or ""
        return None

    def handle_starttag(self, tag, attrs):
        a = dict((k, v or "") for k, v in attrs)

        if tag == "html" and "lang" in a:
            self.data.lang = a["lang"].strip()
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key and "content" in a:
                self.data.meta[key.lower()] = a["content"]
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "canonical" in rel and a.get("href"):
                self.data.canonical = urljoin(self.base_url, a["href"])
            if "stylesheet" in rel:
                self.data.stylesheet_count += 1
        elif tag == "img":
            self.data.images.append(Image(src=a.get("src", ""),
                                          alt=a.get("alt") if "alt" in a else None))
        elif tag == "script":
            self._in_script = True
            if a.get("type", "").lower() == "application/ld+json":
                self.data.has_jsonld = True
            if a.get("src"):
                self.data.script_count += 1
        elif tag == "style":
            self._in_style = True
            self.data.inline_style_blocks += 1
        elif tag in ("input", "select", "textarea"):
            itype = a.get("type", "").lower()
            if tag == "input" and itype in ("hidden", "submit", "button", "image", "reset"):
                pass
            else:
                self.data.total_inputs += 1
                labelled = bool(a.get("aria-label") or a.get("aria-labelledby")
                                or a.get("id") in self._label_for or a.get("title"))
                if not labelled:
                    self.data.inputs_without_label += 1

        if tag == "label":
            f = a.get("for")
            if f:
                self._label_for.add(f)

        if tag in _CAPTURE_TAGS:
            self._cap_stack.append({"tag": tag, "attrs": a, "chars": []})

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        elif tag == "style":
            self._in_style = False

        if tag in _CAPTURE_TAGS:
            for i in range(len(self._cap_stack) - 1, -1, -1):
                if self._cap_stack[i]["tag"] == tag:
                    cap = self._cap_stack.pop(i)
                    text = " ".join("".join(cap["chars"]).split())
                    self._finalize(tag, cap["attrs"], text)
                    break

    def handle_data(self, data):
        if self._in_script:
            self.data.inline_script_bytes += len(data)
            return
        if self._in_style:
            return
        if self._cap_stack:
            self._cap_stack[-1]["chars"].append(data)
        # word count from visible text
        words = data.split()
        if words:
            self.data.word_count += len(words)

    def _finalize(self, tag, attrs, text):
        if tag == "title":
            self.data.title = text or None
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.data.headings.append((int(tag[1]), text))
        elif tag == "a":
            href = attrs.get("href", "").strip()
            if href and not href.startswith(("javascript:", "#")):
                self.data.links.append(
                    Link(href=urljoin(self.base_url, href), text=text,
                         rel=attrs.get("rel", "")))


def parse_html(html: str, base_url: str = "") -> PageData:
    """Parse HTML into PageData. Pure function — safe to unit test."""
    p = _Parser(base_url)
    p.feed(html)
    p.close()
    p.data.html_bytes = len(html.encode("utf-8", "ignore"))
    return p.data


def same_domain(url: str, root: str) -> bool:
    return urlparse(url).netloc == urlparse(root).netloc
