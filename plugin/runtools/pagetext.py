import gzip
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
import urllib.error
import urllib.request
import zlib
from html.parser import HTMLParser

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36 idea-evaluator/0.1"
SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}
DEFAULT_TTL_DAYS = 7
TTL_ENV = "IDEA_EVALUATOR_PAGE_TTL_DAYS"
PUBLISHED_META = ("article:published_time", "og:published_time", "datepublished", "date.published", "pubdate", "publishdate",
                  "publish_date", "publication_date", "citation_publication_date", "citation_date", "dc.date.issued",
                  "dcterms.issued", "dc.date", "sailthru.date", "parsely-pub-date", "date")
MODIFIED_META = ("article:modified_time", "og:updated_time", "datemodified", "dcterms.modified", "last-modified")
BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "header", "footer", "blockquote", "td", "th", "dd", "dt", "pre"}


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "meta":
            a = dict(attrs)
            if a.get("name") in ("description", "og:description") or a.get("property") in ("og:description", "article:published_time"):
                if a.get("content"):
                    self.parts.append("\n" + a["content"] + "\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


class _DateScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.ld = []
        self.times = []
        self._ld = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").strip().lower()
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"].strip())
        elif tag == "script" and "ld+json" in a.get("type", "").lower():
            self._ld = []
        elif tag == "time" and a.get("datetime"):
            self.times.append(((a.get("itemprop") or "").lower(), "pubdate" in a, a["datetime"].strip()))

    def handle_endtag(self, tag):
        if tag == "script" and self._ld is not None:
            self.ld.append("".join(self._ld))
            self._ld = None

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)


DATE_RE = re.compile(r"(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?")
ARCHIVE_STAMP = re.compile(r"^https?://(?:web\.)?archive\.org/web/(\d{4})(\d{2})(\d{2})")


def normalize_date(value):
    m = DATE_RE.search(str(value or ""))
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), m.group(3)
    if not (1990 <= y <= 2100 and 1 <= mo <= 12):
        return None
    if d is None:
        return f"{y:04d}-{mo:02d}"
    d = int(d)
    return f"{y:04d}-{mo:02d}-{d:02d}" if 1 <= d <= 31 else f"{y:04d}-{mo:02d}"


def _ld_dates(blobs):
    found = {}

    def walk(node):
        if isinstance(node, dict):
            for key in ("datePublished", "dateCreated", "uploadDate", "dateModified"):
                if key in node and key not in found:
                    v = normalize_date(node[key])
                    if v:
                        found[key] = v
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for blob in blobs:
        try:
            walk(json.loads(blob.strip()))
        except ValueError:
            continue
    return found


def extract_dates(html, url=None):
    scan = _DateScanner()
    try:
        scan.feed(html or "")
    except Exception:
        pass
    published, source = None, None
    for key in PUBLISHED_META:
        v = normalize_date(scan.meta.get(key))
        if v:
            published, source = v, f"meta {key}"
            break
    ld = _ld_dates(scan.ld)
    if not published:
        for key in ("datePublished", "dateCreated", "uploadDate"):
            if ld.get(key):
                published, source = ld[key], f"json-ld {key}"
                break
    if not published:
        for prop, pub, value in scan.times:
            v = normalize_date(value)
            if v and (prop == "datepublished" or pub):
                published, source = v, "time datePublished"
                break
    modified = None
    for key in MODIFIED_META:
        v = normalize_date(scan.meta.get(key))
        if v:
            modified = v
            break
    modified = modified or ld.get("dateModified")
    m = ARCHIVE_STAMP.match(url or "")
    if m and not published:
        published, source = f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "archive snapshot"
    return {"published": published, "modified": modified, "date_source": source}


def page_date(meta, finding=None):
    if meta and meta.get("published"):
        return {"page_date": meta["published"], "page_date_source": meta.get("date_source"), "page_date_flag": None}
    llm = normalize_date((finding or {}).get("published"))
    if llm:
        return {"page_date": llm, "page_date_source": "finding published (agent-supplied)", "page_date_flag": "llm_fallback"}
    return {"page_date": None, "page_date_source": None, "page_date_flag": "no_date"}


def html_to_text(html):
    p = _Extractor()
    p.feed(html)
    text = "".join(p.parts)
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in text.splitlines()]
    out = []
    for ln in lines:
        if ln or (out and out[-1]):
            out.append(ln)
    return "\n".join(out).strip()


def cache_dir():
    d = os.environ.get("IDEA_EVALUATOR_PAGES") or os.path.join(tempfile.gettempdir(), "idea-evaluator-pages")
    os.makedirs(d, exist_ok=True)
    return d


def _decode(body, encoding_header, charset):
    if encoding_header == "gzip":
        body = gzip.decompress(body)
    elif encoding_header == "deflate":
        body = zlib.decompress(body)
    for enc in (charset, "utf-8", "latin-1"):
        if not enc:
            continue
        try:
            return body.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


def ttl_seconds():
    raw = os.environ.get(TTL_ENV)
    try:
        days = float(raw) if raw not in (None, "") else DEFAULT_TTL_DAYS
    except ValueError:
        days = DEFAULT_TTL_DAYS
    return max(days, 0) * 86400


def _paths(url):
    key = hashlib.sha256((url or "").encode()).hexdigest()[:24]
    return os.path.join(cache_dir(), key + ".txt"), os.path.join(cache_dir(), key + ".json")


def cached_meta(url):
    path, meta_path = _paths(url)
    if not (os.path.exists(path) and os.path.exists(meta_path)):
        return None
    try:
        with open(meta_path) as f:
            meta = json.load(f)
    except (OSError, ValueError):
        return None
    return meta if isinstance(meta, dict) else None


def is_fresh(meta, now=None):
    stamp = meta.get("fetched_at_epoch") if isinstance(meta, dict) else None
    if not isinstance(stamp, (int, float)):
        return False
    return (now or time.time()) - stamp <= ttl_seconds()


def fetch(url, timeout=30, opener=None, fresh=False, now=None):
    path, meta_path = _paths(url)
    if not fresh:
        meta = cached_meta(url)
        if meta is not None and is_fresh(meta, now):
            meta["cached"] = True
            return meta
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain,application/json;q=0.9,*/*;q=0.5", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en,*;q=0.5"})
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read()
            enc = resp.headers.get("Content-Encoding", "")
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False, "path": None, "error": f"http {e.code}"}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "path": None, "error": type(e).__name__ + ": " + str(e)[:200]}
    charset = None
    m = re.search(r"charset=([\w-]+)", ctype)
    if m:
        charset = m.group(1)
    if "pdf" in ctype:
        return {"url": url, "status": status, "ok": False, "path": None, "error": "pdf not supported"}
    raw = _decode(body, enc, charset)
    is_html = "html" in ctype or "<html" in raw[:2000].lower()
    text = html_to_text(raw) if is_html else raw
    dates = extract_dates(raw, url) if is_html else extract_dates("", url)
    stamp = now or time.time()
    with open(path, "w") as f:
        f.write(text)
    meta = {"url": url, "status": status, "ok": bool(text.strip()), "path": path, "chars": len(text),
            "error": None if text.strip() else "empty page",
            "fetched_at": datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fetched_at_epoch": stamp, **dates}
    with open(meta_path, "w") as f:
        json.dump(meta, f)
    meta["cached"] = False
    return meta


def normalize(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("­", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _bare(s):
    s = re.sub(r"[^\w\s%$£€+/-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def quote_in_text(quote, text):
    q = normalize(quote)
    t = _bare(normalize(text))
    parts = [_bare(p) for p in re.split(r"\.\.\.|…|\[\.\.\.\]", q)]
    parts = [p for p in parts if p]
    if not parts:
        return False
    pos = 0
    for p in parts:
        i = t.find(p, pos)
        if i < 0:
            return False
        pos = i + len(p)
    return True


def check_quote(url, quote, opener=None):
    meta = fetch(url, opener=opener)
    if not meta.get("ok"):
        return {"result": "fetch_failed", "url": url, "error": meta.get("error"), "status": meta.get("status")}
    with open(meta["path"]) as f:
        text = f.read()
    found = quote_in_text(quote, text)
    return {"result": "found" if found else "not_found", "url": url, "path": meta["path"], "status": meta.get("status"),
            "fetched_at": meta.get("fetched_at"), "published": meta.get("published"), "date_source": meta.get("date_source")}


def recheck_quote(url, quote, opener=None, now=None):
    before = cached_text(url)
    had = bool(before) and quote_in_text(quote, before)
    meta = fetch(url, opener=opener, fresh=True, now=now)
    if not meta.get("ok"):
        old = cached_meta(url) or {}
        result = "found" if had else ("not_found" if before else "fetch_failed")
        return {"result": result, "live": "fetch_failed", "url": url, "error": meta.get("error"), "status": meta.get("status"),
                "text": before, "fetched_at": old.get("fetched_at"), "published": old.get("published"),
                "modified": old.get("modified"), "date_source": old.get("date_source")}
    with open(meta["path"]) as f:
        text = f.read()
    now_found = quote_in_text(quote, text)
    result = "found" if now_found else ("gone" if had else "not_found")
    return {"result": result, "live": "fetched", "url": url, "status": meta.get("status"), "text": text,
            "fetched_at": meta.get("fetched_at"), "published": meta.get("published"), "modified": meta.get("modified"),
            "date_source": meta.get("date_source"), "cached_copy_had_quote": had}


QUALIFIERS = re.compile(
    r"(?<!\w)(except|unless|provided that|only if|other than|excluding|apart from|with the exception|but|however|"
    r"крім|окрім|за винятком|але|проте|однак|якщо|за умови|лише якщо|втім|хоча|"
    r"кроме|за исключением|но|однако|если|при условии|"
    r"außer|ausgenommen|es sei denn|sofern|aber|jedoch|"
    r"z wyjątkiem|chyba że|ale|jednak|oprócz)(?!\w)")


def cached_text(url):
    path, _ = _paths(url)
    if not os.path.exists(path):
        return None
    with open(path, errors="ignore") as f:
        return f.read()


SENTENCE_END = re.compile(r"(?<=[.!?…])[\"'»”)\]]*\s+|\n+")


def sentences(text):
    out, pos = [], 0
    for m in SENTENCE_END.finditer(text or ""):
        seg = text[pos:m.start()].strip()
        if seg:
            out.append(seg)
        pos = m.end()
    tail = (text or "")[pos:].strip()
    if tail:
        out.append(tail)
    return out


def quote_window(quote, text, radius=2):
    sents = sentences(text)
    if not sents:
        return None
    parts = [_bare(p) for p in re.split(r"\.\.\.|…|\[\.\.\.\]", normalize(quote or ""))]
    parts = [p for p in parts if p]
    if not parts:
        return None
    bare, offsets, pos = [], [], 0
    for s in sents:
        b = _bare(normalize(s))
        offsets.append((pos, pos + len(b)))
        bare.append(b)
        pos += len(b) + 1
    joined = " ".join(bare)
    start = end = None
    cursor = 0
    for p in parts:
        i = joined.find(p, cursor)
        if i < 0:
            return None
        if start is None:
            start = i
        end = i + len(p)
        cursor = end
    first = next(k for k, (a, b) in enumerate(offsets) if b >= start)
    last = next(k for k, (a, b) in enumerate(offsets) if b >= end)
    lo, hi = max(0, first - radius), min(len(sents), last + radius + 1)
    return {"before": sents[lo:first], "quote_sentences": sents[first:last + 1], "after": sents[last + 1:hi],
            "text": " ".join(sents[lo:hi])}


def cut_qualifier(quote, text):
    t = normalize(text or "")
    segs = [normalize(s) for s in re.split(r"\.\.\.|…|\[\.\.\.\]", quote or "") if normalize(s)]
    if not segs or not t:
        return None
    last = segs[-1].rstrip(" .;:,")
    i = t.find(last)
    if i < 0 or not last:
        return None
    rest = t[i + len(last):]
    m = re.search(r"[.!?\n]", rest)
    clause = (rest[:m.start()] if m else rest)[:300].strip(" ,;:-")
    if clause and QUALIFIERS.search(clause):
        return clause[:160]
    return None
