import json
import math
import re
from difflib import SequenceMatcher
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "directory"
META = "meta.json"
SHARDS = "companies-*.jsonl"
FAILURE_URL = re.compile(r"(failory\.com/|kaggle\.com/datasets/|cbinsights\.com/research/|startups\.rip|lootdrop\.com|autopsy\.io)", re.I)
DEAD = {"dead", "inactive", "closed"}
FAILURE_IDS = {"failory", "kaggle", "cbinsights"}
ALIVE = {"active", "public", "operating"}
SUFFIXES = {"inc", "incorporated", "ltd", "limited", "llc", "corp", "corporation", "co", "company", "gmbh", "sa", "sas", "srl", "bv", "plc", "ag", "oy", "ab", "pty"}
STOP = {"a", "an", "and", "the", "of", "for", "to", "in", "on", "with", "by", "from", "at", "or", "as", "is", "your", "that", "via", "app", "platform"}
MONTH = re.compile(r"^\d{4}-\d{2}$")
NOTE = "directory rows are leads, not findings: open a source URL, copy the quote from the page and run check-quote before citing it"
EMPTY = "no row in the local company directory matches; search the web and failure collections as usual"

_cache = {}


def norm_name(s):
    s = str(s or "").lower().replace("&", " and ")
    words = re.sub(r"[^\w]+", " ", s).split()
    while len(words) > 1 and words[-1] in SUFFIXES:
        words.pop()
    return " ".join(words)


def norm_domain(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"^[a-z]+://", "", s).split("/")[0].split("?")[0].split(":")[0]
    return s[4:] if s.startswith("www.") else s


def tokens(s):
    out = []
    for w in re.sub(r"[^\w]+", " ", str(s or "").lower()).split():
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def month(v):
    m = re.search(r"(\d{4})(?:-(\d{2}))?", str(v or ""))
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2) or '12'}"


def year(v):
    m = re.search(r"(\d{4})", str(v or ""))
    return int(m.group(1)) if m else None


def is_failure_url(url):
    return bool(FAILURE_URL.search(str(url or "")))


def timeline_problems(rec, now_year=None):
    out = []
    f, d = year(rec.get("founded")), year(rec.get("died"))
    if f is not None and d is not None and f > d:
        out.append(f"founded {f} after died {d}")
    if f is not None and now_year and f > now_year:
        out.append(f"founded {f} in the future")
    if d is not None and now_year and d > now_year:
        out.append(f"died {d} in the future")
    if d is not None and str(rec.get("status") or "").lower() in ALIVE:
        out.append(f"status {rec.get('status')} but died {d}")
    return out


def load(path=None):
    path = Path(path or DATA)
    key = str(path)
    if key not in _cache:
        with open(path / META, encoding="utf-8") as f:
            data = json.load(f)
        rows = []
        for shard in sorted(path.glob(SHARDS)):
            with open(shard, encoding="utf-8") as f:
                rows += [json.loads(line) for line in f if line.strip()]
        data["companies"] = rows
        for r in rows:
            r["_n"] = norm_name(r.get("name"))
            r["_t"] = set(tokens(" ".join(str(r.get(k) or "") for k in ("name", "does", "death_cause"))))
        df = {}
        for r in rows:
            for t in r["_t"]:
                df[t] = df.get(t, 0) + 1
        n = max(len(rows), 1)
        data["_idf"] = {t: math.log(1 + n / c) for t, c in df.items()}
        _cache[key] = data
    return _cache[key]


def mask(rec, as_of, status_as_of=None):
    out = {k: v for k, v in rec.items() if not k.startswith("_")}
    founded = month(out.get("founded"))
    if as_of and founded and founded > as_of:
        return None
    if not as_of:
        return out
    died = month(out.get("died"))
    dead_by_then = bool(died and died <= as_of)
    if dead_by_then:
        out["status"] = "dead"
    else:
        for k in ("died", "death_cause"):
            out.pop(k, None)
        if not (status_as_of and as_of >= status_as_of):
            out.pop("status", None)
    if not dead_by_then and str(out.get("status") or "").lower() not in DEAD:
        if out.get("url") and is_failure_url(out["url"]):
            out.pop("url")
        if isinstance(out.get("sources"), list):
            out["sources"] = [u for u in out["sources"] if not is_failure_url(u)]
        if isinstance(out.get("source_ids"), list):
            out["source_ids"] = [x for x in out["source_ids"] if x not in FAILURE_IDS]
        out.pop("origin", None)
        if rec.get("sources") and not out.get("sources"):
            return None
    return {k: v for k, v in out.items() if v not in (None, "", [])}


def counters(matches):
    dead = sum(1 for x in matches if str(x.get("status") or "").lower() in DEAD or x.get("died"))
    alive = sum(1 for x in matches if not x.get("died") and str(x.get("status") or "").lower() in ALIVE)
    acquired = sum(1 for x in matches if not x.get("died") and str(x.get("status") or "").lower() == "acquired")
    return {"dead": dead, "alive": alive, "acquired": acquired, "unknown": len(matches) - dead - alive - acquired}


def _now_year(data):
    return year(data.get("built"))


def _result(data, query, as_of, scored, limit):
    status_as_of = data.get("status_as_of")
    matches = []
    for rec, how, score in scored:
        m = mask(rec, as_of, status_as_of)
        if m is None:
            continue
        m["match"] = how
        if score is not None:
            m["score"] = round(score, 3)
        problems = timeline_problems(rec, _now_year(data))
        if problems:
            m["warnings"] = problems
        matches.append(m)
        if len(matches) >= limit:
            break
    out = {"query": query, "as_of": as_of, "directory_built": data.get("built"), "status_as_of": status_as_of, "matches": matches, "counts": counters(matches)}
    out["note"] = NOTE if matches else EMPTY
    return out


def by_name(name, as_of, limit=5, fuzzy=0.86, path=None):
    data = load(path)
    q = norm_name(name)
    scored = [(r, "exact", None) for r in data["companies"] if q and r["_n"] == q]
    if not scored and q:
        cands = []
        for r in data["companies"]:
            n = r["_n"]
            if not n:
                continue
            sm = SequenceMatcher(None, q, n)
            if sm.real_quick_ratio() < fuzzy or sm.quick_ratio() < fuzzy:
                continue
            s = sm.ratio()
            if s >= fuzzy:
                cands.append((r, "fuzzy", s))
        cands.sort(key=lambda x: -x[2])
        scored = cands
    return _result(data, {"name": name}, as_of, scored, limit)


def by_domain(domain, as_of, limit=5, path=None):
    data = load(path)
    d = norm_domain(domain)
    scored = [(r, "domain", None) for r in data["companies"] if d and norm_domain(r.get("domain")) == d]
    return _result(data, {"domain": domain}, as_of, scored, limit)


def search(text, as_of, limit=15, dead_only=False, min_score=0.34, path=None):
    data = load(path)
    idf = data["_idf"]
    q = set(tokens(text))
    total = sum(idf.get(t, 0.0) for t in q)
    scored = []
    if total > 0:
        for r in data["companies"]:
            hit = q & r["_t"]
            if not hit:
                continue
            s = sum(idf.get(t, 0.0) for t in hit) / total
            if s >= min_score:
                scored.append((r, "words", s))
        scored.sort(key=lambda x: -x[2])
    if dead_only:
        status_as_of = data.get("status_as_of")
        keep = []
        for rec, how, s in scored:
            m = mask(rec, as_of, status_as_of)
            if m is not None and (m.get("died") or str(m.get("status") or "").lower() in DEAD):
                keep.append((rec, how, s))
        scored = keep
    return _result(data, {"text": text, "dead_only": dead_only}, as_of, scored, limit)


def info(path=None):
    data = load(path)
    return {k: v for k, v in data.items() if k not in ("companies", "_idf")} | {"companies": len(data["companies"])}


def valid_as_of(v):
    return bool(MONTH.match(str(v or "")))
