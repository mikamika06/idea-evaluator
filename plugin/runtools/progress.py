import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

from runtools.session import load_text, mentions, run_dirs

try:
    import fcntl
except ImportError:
    fcntl = None

TOTAL = 7
STATE_FILE = ".progress.json"
LOCK_FILE = ".progress.lock"
MAX_AGE_SECONDS = 12 * 3600
DONE_GRACE_SECONDS = 1800
RUN_DIR_ENV = "IDEA_EVALUATOR_RUN_DIR"
QUESTIONS = [f"q{i}.json" for i in range(1, 8)]
PASS1 = ["dossier.json", "law.json", "q3-competitors.json", "q3-graveyard.json"] + QUESTIONS
LANG_RE = re.compile(r"OUTPUT_LANGUAGE:[ \t]*([^\s\"'`\\\],|)<>]+)")
PRICE_RE = re.compile(
    r"(?:US\$|\$|€|£|₴|USD|EUR|GBP|UAH|PLN)\s?\d[\d,.]*(?:\s?[kKmM]\b)?(?:\s?(?:/|per|a)\s?(?:day|week|month|year|mo|yr|user|seat|unit|hour|order|visit|km|kg|piece|lesson|session)\b)?"
    r"|\d[\d,.]*\s?(?:USD|EUR|GBP|UAH|PLN|грн|€|\$)(?:\s?(?:/|per|a)\s?(?:day|week|month|year|mo|yr|user|seat|unit|hour|order)\b)?"
    r"|\bfree(?:mium)?\b",
    re.IGNORECASE,
)

NAMES = {
    "en": {
        "KP1": "consumer tarpit", "KP2": "a free or built-in substitute already satisfies people",
        "KP3": "the platform or leader already ships it", "KP4": "price above what the payer pays now",
        "KP5": "the same model already died", "KP6": "nobody pays", "KP7": "law forbids it",
        "KP8": "users resigned to the problem", "KP9": "tiny market ceiling", "KP10": "two-sided cold start",
        "KP11": "the trigger is gone", "KP12": "deals leak past the platform", "KP13": "the payer earns from the problem",
        "KP14": "buyers want a person or the result, not a tool", "KP15": "cost to serve eats the price",
        "KP16": "each customer needs its own integration", "KP17": "one-off or rare job", "KP18": "fad without hold",
        "AS1": "buyers already pay for a worse substitute", "AS2": "a mandate in force", "AS3": "measurable pull",
        "AS4": "crowded but disliked", "AS5": "the same model works elsewhere",
        "AS6": "a dated change removed the old cause of death", "AS7": "proven short-video channel",
    },
    "uk": {
        "KP1": "споживча пастка", "KP2": "безкоштовна чи вбудована заміна вже влаштовує людей",
        "KP3": "платформа чи лідер ринку вже це робить", "KP4": "ціна вища, ніж платник платить зараз",
        "KP5": "така сама модель уже помирала", "KP6": "ніхто не платить", "KP7": "закон забороняє",
        "KP8": "люди змирилися з проблемою", "KP9": "замала стеля ринку", "KP10": "холодний старт двосторонньої платформи",
        "KP11": "зник тригер попиту", "KP12": "угоди йдуть повз платформу", "KP13": "платник заробляє на проблемі",
        "KP14": "покупець хоче людину або готовий результат, а не інструмент",
        "KP15": "собівартість обслуговування з'їдає ціну", "KP16": "кожен клієнт потребує окремої інтеграції",
        "KP17": "разова чи рідкісна потреба", "KP18": "мода без утримання",
        "AS1": "покупці вже платять за гіршу заміну", "AS2": "чинна обов'язкова вимога", "AS3": "вимірюваний попит",
        "AS4": "тісно, але конкурентів не люблять", "AS5": "така модель працює деінде",
        "AS6": "датована зміна прибрала давню причину смерті", "AS7": "доведений канал коротких відео",
    },
}

T = {
    "en": {
        "stage": {1: "Idea card", 2: "Research, pass 1", 3: "Reconcile and pass 2", 4: "Kill check",
                  5: "Audit and support check", 6: "Verdict and judge", 7: "Report"},
        "done": "done", "skipped": "skipped", "from_saved": "taken from the saved run",
        "min": "m", "sec": "s",
        "customer": "Customer", "payer": "Payer", "market": "Market", "price": "Price", "sold": "Sold",
        "kind": "Business kind", "assumed": "Assumed (not in the idea text)", "depth": "Depth",
        "findings": "Findings: {n}, verified quotes {v}",
        "competitors": "Competitors: {n} ({d} direct)", "no_competitors": "Competitors: none found",
        "price_unknown": "price not stated",
        "dead": "Dead attempts: {n}", "no_dead": "Dead attempts: none found",
        "pays": "Who pays now", "payer_exists": "payer exists: {v}", "pays_today": "pays today for similar: {v}",
        "flags": "Red flags warming up", "at_threshold": "already at threshold", "below": "not yet proven",
        "signals": "Live signals", "no_flags": "Red flags warming up: none", "no_signals": "Live signals: none",
        "contradictions": "Contradictions between answers: {n} ({d} sent to pass 2)",
        "deep": "Pass 2 deepened", "no_deep": "Pass 2: not needed",
        "added": "Pass 2 added {n} findings, {t} in all",
        "loop": "Loop", "early": "early exit on a strong red flag",
        "causes": "Causes of death checked: {n} (supported {s}, refuted {r}, not found {f})",
        "supported": "Supported", "refuted": "Refuted",
        "k_findings": "New kill-check findings: {n}",
        "kill_skipped": "sheet already killed by a verified strong red flag, or early exit",
        "quotes": "Quotes rechecked: {f} of {n} found on the page",
        "quotes_bad": "not found {nf}, gone {g}, fetch failed {ff}",
        "claims": "Decisive claims: holds {h}, weak {w}, fails {f}",
        "support": "Quote context: supports {s}, partial {p}, dropped {d}",
        "dropped": "Dropped",
        "verdict": "Verdict", "rule": "Rule", "fired": "Red flags fired", "alive": "Alive signals",
        "judge": "Judge", "agrees": "agrees", "disagrees": "disagrees, own opinion {v}",
        "changes": "sheet changes after the judge: {n}", "disputed": "disputed",
        "need": "Need",
        "report": "Report", "risk": "Riskiest assumption", "test": "Cheapest test", "collect": "Facts to collect: {n}",
        "none": "none",
    },
    "uk": {
        "stage": {1: "Картка ідеї", 2: "Дослідження, перший прохід", 3: "Звірка і другий прохід",
                  4: "Пошук причини смерті", 5: "Аудит цитат і контексту", 6: "Вердикт і суддя", 7: "Звіт"},
        "done": "готово", "skipped": "пропущено", "from_saved": "взято із збереженого запуску",
        "min": " хв", "sec": " с",
        "customer": "Клієнт", "payer": "Платник", "market": "Ринок", "price": "Ціна", "sold": "Продаж",
        "kind": "Тип бізнесу", "assumed": "Припущено (у тексті ідеї цього нема)", "depth": "Глибина",
        "findings": "Знахідок: {n}, цитат підтверджено на сторінці: {v}",
        "competitors": "Конкурентів: {n} (прямих {d})", "no_competitors": "Конкурентів не знайдено",
        "price_unknown": "ціна не вказана",
        "dead": "Мертвих спроб: {n}", "no_dead": "Мертвих спроб не знайдено",
        "pays": "Хто платить зараз", "payer_exists": "платник є: {v}", "pays_today": "уже платить за схоже: {v}",
        "flags": "Червоні прапори, що гріються", "at_threshold": "уже на порозі", "below": "ще не доведено",
        "signals": "Живі сигнали", "no_flags": "Червоних прапорів поки нема", "no_signals": "Живих сигналів поки нема",
        "contradictions": "Суперечностей між відповідями: {n} (на другий прохід {d})",
        "deep": "Другий прохід поглибив", "no_deep": "Другий прохід не потрібен",
        "added": "Другий прохід додав {n} знахідок, усього {t}",
        "loop": "Петля", "early": "ранній вихід на сильному червоному прапорі",
        "causes": "Перевірено причин смерті: {n} (підтверджено {s}, спростовано {r}, не знайдено {f})",
        "supported": "Підтверджено", "refuted": "Спростовано",
        "k_findings": "Нових знахідок перевірки: {n}",
        "kill_skipped": "таблицю вже вбив підтверджений сильний прапор, або ранній вихід",
        "quotes": "Цитат перевірено наживо: знайдено {f} з {n}",
        "quotes_bad": "не знайдено {nf}, зникло {g}, сторінка не відкрилась {ff}",
        "claims": "Вирішальні твердження: тримаються {h}, слабкі {w}, падають {f}",
        "support": "Контекст цитат: підтримує {s}, частково {p}, відкинуто {d}",
        "dropped": "Відкинуто",
        "verdict": "Вердикт", "rule": "Правило", "fired": "Спрацювали червоні прапори", "alive": "Живі сигнали",
        "judge": "Суддя", "agrees": "згоден", "disagrees": "не згоден, його думка {v}",
        "changes": "змін таблиці після судді: {n}", "disputed": "спірний",
        "need": "Потреба",
        "report": "Звіт", "risk": "Найризикованіше припущення", "test": "Найдешевший тест", "collect": "Фактів дозібрати: {n}",
        "none": "нема",
    },
}

RULES = {
    "en": {"D1": "one strong red flag at threshold with no allowed rebuttal",
           "D2": "three or more independent red flags and nobody pays for a substitute",
           "A1": "a pull signal with a number and no fatal red flag",
           "I1": "evidence is thin or mixed", "J1": "the sheet said DEAD, the judge disagreed"},
    "uk": {"D1": "один сильний червоний прапор на порозі без дозволеного спростування",
           "D2": "три і більше незалежних червоних прапори, і ніхто не платить за заміну",
           "A1": "сигнал попиту з числом і жодного фатального прапора",
           "I1": "доказів замало або вони суперечливі", "J1": "таблиця дала DEAD, суддя не погодився"},
}

VERDICTS = {"uk": {"DEAD": "DEAD (мертва)", "ALIVE": "ALIVE (жива)", "INSUFFICIENT_DATA": "INSUFFICIENT_DATA (замало даних)"}}
VALUES = {"uk": {"yes": "так", "no": "ні", "unknown": "невідомо", "consumer": "споживач", "business": "бізнес",
                 "government": "держава", "solo_professional": "самозайнятий фахівець", "self_serve": "самообслуговування",
                 "sales_led": "через продажників", "tender": "тендер", "dealer": "через дилерів", "venture": "венчурний",
                 "small_business": "малий бізнес", "grant": "грантовий", "social": "соціальний", "defence": "оборонний",
                 "under_2k": "до $2k на рік", "2k_10k": "$2-10k на рік", "10k_25k": "$10-25k на рік", "over_25k": "понад $25k на рік",
                 "calibration": "калібрувальна", "full": "повна", "batch": "пакетний", "interactive": "інтерактивний",
                 "none": "нема", "pain_elsewhere": "біль деінде", "segment_no_money": "сегмент без грошей"}}


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data


def _dict(path):
    data = _load(path)
    return data if isinstance(data, dict) else {}


def _exists(run_dir, name):
    return os.path.exists(os.path.join(run_dir, name))


def _cut(text, n):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _v(lang, value):
    return VALUES.get(lang, {}).get(str(value), str(value))


def _name(lang, code):
    return NAMES[lang].get(code, "")


def _coded(lang, code):
    name = _name(lang, code)
    return f"{name} ({code})" if name else str(code)


def findings(run_dir):
    rows = {}
    path = os.path.join(run_dir, "findings.jsonl")
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and row.get("finding_id"):
                    rows.setdefault(row["finding_id"], row)
    except OSError:
        pass
    return rows


def _verified(rows):
    return sum(1 for r in rows.values() if r.get("opened") is True and r.get("quote_check") == "found")


def _judged(run_dir):
    v = _dict(os.path.join(run_dir, "verdict.json"))
    return isinstance(v.get("judge"), dict) and v["judge"].get("agrees") is not None


def stage_status(run_dir, n, run):
    e = lambda name: _exists(run_dir, name)
    early = run.get("early_exit") is True
    if n == 1:
        return "done" if e("card.json") and not run.get("awaiting") else None
    if n == 2:
        return "done" if all(e(f) for f in PASS1 + ["q3.json", "findings.jsonl"]) else None
    if n == 3:
        if e("reconcile.json"):
            deep = _dict(os.path.join(run_dir, "reconcile.json")).get("deep_pass") or []
            if not deep or any(e(f) for f in ("verdict.draft.json", "killcheck.json", "support.json", "verdict.json")):
                return "done"
            return None
        if (early and e("support.json")) or e("verdict.json"):
            return "skipped"
        return None
    if n == 4:
        if e("killcheck.json"):
            return "done"
        if (early and e("support.json")) or e("judge.json") or e("verdict.prejudge.json"):
            return "skipped"
        return None
    if n == 5:
        return "done" if e("audit.json") and e("support.json") else None
    if n == 6:
        return "done" if e("judge.json") and (_judged(run_dir) or e("report.md")) else None
    if n == 7:
        return "done" if e("report.md") else None
    return None


def _elapsed(run, lang, now):
    try:
        start = datetime.strptime(str(run.get("started_at")), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return ""
    secs = max(0, int(now - start))
    t = T[lang]
    return f"{secs // 60}{t['min']} {secs % 60:02d}{t['sec']}"


def _header(lang, n, status, run, now):
    t = T[lang]
    word = t["done"] if status == "done" else t["skipped"]
    el = _elapsed(run, lang, now)
    return f"[idea-evaluator {n}/{TOTAL}] {t['stage'][n]}: {word}" + (f" · {el}" if el else "")


def _card_lines(run_dir, run, lang):
    t = T[lang]
    card = _dict(os.path.join(run_dir, "card.v2.json")) or _dict(os.path.join(run_dir, "card.json"))
    lines = [_cut(card.get("summary_third_person"), 260)]
    places = ", ".join((card.get("jurisdiction") or {}).get("places") or [])
    lines.append(f"{t['customer']}: {_v(lang, card.get('customer'))} · {t['payer']}: {_cut(card.get('payer_description'), 90)}")
    price = _v(lang, card.get("price_band"))
    unit = _cut(card.get("price_unit"), 90)
    lines.append(f"{t['market']}: {places or '?'} · {t['price']}: {price}" + (f" ({unit})" if unit else ""))
    lines.append(f"{t['sold']}: {_v(lang, card.get('sales_motion'))} · {t['kind']}: {_v(lang, card.get('trajectory'))} · {t['depth']}: {_v(lang, run.get('depth'))}, {_v(lang, run.get('mode'))}")
    notes = card.get("facet_notes") or {}
    assumed = [k for k, v in notes.items() if "assumed" in str(v).lower()]
    if assumed:
        lines.append(f"{t['assumed']}: {', '.join(assumed)}")
    return lines


def _price(text):
    m = PRICE_RE.search(str(text or ""))
    return m.group(0).strip() if m else None


def _candidates(run_dir, key):
    out = {}
    for name in QUESTIONS + ["dossier.json", "q3-competitors.json", "q3-graveyard.json"]:
        card = _dict(os.path.join(run_dir, name))
        for c in card.get(key) or []:
            if isinstance(c, dict) and c.get("code"):
                prev = out.get(c["code"])
                if prev is None or (c.get("threshold_met") and not prev.get("threshold_met")) or (c.get("number") and not prev.get("number")):
                    out[c["code"]] = c
    law = _dict(os.path.join(run_dir, "law.json")).get("kill_candidate")
    if key == "kill_candidates" and isinstance(law, dict) and law.get("code") and law["code"] not in out:
        out[law["code"]] = law
    return out


def _code_key(code):
    m = re.search(r"\d+", str(code))
    return int(m.group(0)) if m else 99


def _research_lines(run_dir, lang, rows):
    t = T[lang]
    lines = [t["findings"].format(n=len(rows), v=_verified(rows))]
    q3 = _dict(os.path.join(run_dir, "q3.json"))
    comps = [c for c in q3.get("competitors") or [] if isinstance(c, dict)]
    if comps:
        order = {"direct": 0, "partial": 1, "substitute": 2}
        ranked = sorted(comps, key=lambda c: (order.get(c.get("relation"), 3), 0 if c.get("alive") == "yes" else 1))
        direct = sum(1 for c in comps if c.get("relation") == "direct")
        parts = []
        for c in ranked[:3]:
            price = _price(c.get("what")) or t["price_unknown"]
            url = c.get("url") or ""
            parts.append(f"{_cut(c.get('name'), 40)} ({price})" + (f" {url}" if url else ""))
        lines.append(t["competitors"].format(n=len(comps), d=direct) + ": " + "; ".join(parts))
    else:
        lines.append(t["no_competitors"])
    dead = [d for d in q3.get("dead_attempts") or [] if isinstance(d, dict)]
    if dead:
        ranked = sorted(dead, key=lambda d: {"yes": 0, "partly": 1}.get(d.get("same_idea"), 2))
        parts = [f"{_cut(d.get('name'), 40)} {d.get('years') or ''}: {_cut(d.get('cause'), 90)}".replace("  ", " ") for d in ranked[:2]]
        lines.append(t["dead"].format(n=len(dead)) + ": " + "; ".join(parts))
    else:
        lines.append(t["no_dead"])
    q4 = _dict(os.path.join(run_dir, "q4.json"))
    payer = q4.get("payer") or {}
    q2 = _dict(os.path.join(run_dir, "q2.json"))
    spend = [f"{_cut(s.get('what'), 60)}: {_cut(s.get('spend'), 70)}" for s in q2.get("current_solutions") or [] if isinstance(s, dict) and s.get("spend")]
    pays = [f"{_cut(payer.get('who'), 60)}"] if payer.get("who") else []
    pays.append(t["payer_exists"].format(v=_v(lang, q4.get("payer_exists", "unknown"))))
    pays.append(t["pays_today"].format(v=_v(lang, payer.get("pays_today_for_similar", "unknown"))))
    if payer.get("budget_line"):
        pays.append(_cut(payer.get("budget_line"), 70))
    lines.append(f"{t['pays']}: " + ", ".join(pays) + ("; " + "; ".join(spend[:2]) if spend else ""))
    kills = _candidates(run_dir, "kill_candidates")
    if kills:
        ranked = sorted(kills.values(), key=lambda c: (0 if c.get("threshold_met") else 1, _code_key(c.get("code"))))
        parts = [f"{_coded(lang, c['code'])} {t['at_threshold'] if c.get('threshold_met') else t['below']}" for c in ranked[:5]]
        lines.append(f"{t['flags']}: " + "; ".join(parts))
    else:
        lines.append(t["no_flags"])
    alive = _candidates(run_dir, "alive_candidates")
    if alive:
        ranked = sorted(alive.values(), key=lambda c: (0 if c.get("number") else 1, _code_key(c.get("code"))))
        parts = [_coded(lang, c["code"]) + (f": {_cut(c.get('number'), 70)}" if c.get("number") else "") for c in ranked[:4]]
        lines.append(f"{t['signals']}: " + "; ".join(parts))
    else:
        lines.append(t["no_signals"])
    return lines


def _reconcile_lines(run_dir, run, lang, rows, state):
    t = T[lang]
    rec = _dict(os.path.join(run_dir, "reconcile.json"))
    contr = [c for c in rec.get("contradictions") or [] if isinstance(c, dict)]
    sent = sum(1 for c in contr if c.get("resolution") == "deep_pass")
    lines = [t["contradictions"].format(n=len(contr), d=sent)]
    deep = [d for d in rec.get("deep_pass") or [] if isinstance(d, dict)]
    if deep:
        lines.append(f"{t['deep']}: " + "; ".join(f"{d.get('question')}: {_cut(d.get('focus'), 110)}" for d in deep[:3]))
        before = state.get("findings_after_pass1")
        if isinstance(before, int):
            lines.append(t["added"].format(n=max(0, len(rows) - before), t=len(rows)))
    else:
        lines.append(t["no_deep"])
    loop = rec.get("loop") or {}
    if isinstance(loop, dict) and loop.get("kind"):
        lines.append(f"{t['loop']}: {_v(lang, loop.get('kind'))}" + (f" ({_cut(loop.get('reason'), 120)})" if loop.get("kind") != "none" else ""))
    return lines


def _kill_lines(run_dir, lang, rows):
    t = T[lang]
    kc = _dict(os.path.join(run_dir, "killcheck.json"))
    causes = [c for c in kc.get("causes") or [] if isinstance(c, dict)]
    count = {s: sum(1 for c in causes if c.get("status") == s) for s in ("supported", "refuted", "not_found")}
    lines = [t["causes"].format(n=len(causes), s=count["supported"], r=count["refuted"], f=count["not_found"])]
    sup = [c for c in causes if c.get("status") == "supported"]
    if sup:
        lines.append(f"{t['supported']}: " + "; ".join(f"{_coded(lang, c.get('pattern'))}: {_cut(c.get('cause'), 90)}" for c in sup[:3]))
    ref = [c for c in causes if c.get("status") == "refuted"]
    if ref:
        lines.append(f"{t['refuted']}: " + "; ".join(_coded(lang, c.get("pattern")) for c in ref[:4]))
    ids = {fid for fid in rows if str(fid).startswith("K-")}
    try:
        with open(os.path.join(run_dir, "findings-killer-scout.jsonl"), encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.search(r'"finding_id"\s*:\s*"(K-[^"]+)"', line)
                if m:
                    ids.add(m.group(1))
    except OSError:
        pass
    lines.append(t["k_findings"].format(n=len(ids)))
    return lines


def _audit_lines(run_dir, lang):
    t = T[lang]
    audit = _dict(os.path.join(run_dir, "audit.json"))
    checked = [c for c in audit.get("checked") or [] if isinstance(c, dict)]
    qc = [c.get("quote_check") for c in checked]
    lines = [t["quotes"].format(f=qc.count("found"), n=len(checked))]
    if len(checked) != qc.count("found"):
        lines[0] += " (" + t["quotes_bad"].format(nf=qc.count("not_found"), g=qc.count("gone"), ff=qc.count("fetch_failed")) + ")"
    claims = [c for c in audit.get("decisive_claims") or [] if isinstance(c, dict)]
    by = {v: [str(c.get("code")) for c in claims if c.get("verdict") == v] for v in ("holds", "weak", "fails")}
    lines.append(t["claims"].format(h=f"{len(by['holds'])} [{', '.join(by['holds'])}]" if by["holds"] else 0,
                                    w=f"{len(by['weak'])} [{', '.join(by['weak'])}]" if by["weak"] else 0,
                                    f=f"{len(by['fails'])} [{', '.join(by['fails'])}]" if by["fails"] else 0))
    checks = [c for c in _dict(os.path.join(run_dir, "support.json")).get("checks") or [] if isinstance(c, dict)]
    labels = [c.get("label") for c in checks]
    dropped = [c for c in checks if c.get("label") in ("does_not_support", "truncated_qualifier")]
    lines.append(t["support"].format(s=labels.count("supports"), p=labels.count("partial"), d=len(dropped)))
    if dropped:
        lines.append(f"{t['dropped']}: " + "; ".join(f"{c.get('code')} {c.get('finding_id')}: {_cut(c.get('reason'), 80)}" for c in dropped[:3]))
    return lines


def _verdict_lines(run_dir, lang):
    t = T[lang]
    v = _dict(os.path.join(run_dir, "verdict.json"))
    verdict = VERDICTS.get(lang, {}).get(v.get("verdict"), v.get("verdict"))
    rule = v.get("rule_fired")
    lines = [f"{t['verdict']}: {verdict} · p_survive {v.get('p_survive')}" + (f" · {t['disputed']}" if v.get("disputed") else ""),
             f"{t['rule']} {rule}: {RULES[lang].get(rule, '')}"]
    fired = [p for p in v.get("patterns") or [] if isinstance(p, dict) and p.get("fired")]
    if fired:
        fired.sort(key=lambda p: (0 if p.get("threshold_met") else 1, _code_key(p.get("code"))))
        lines.append(f"{t['fired']}: " + "; ".join(_coded(lang, p.get("code")) + (f" {t['at_threshold']}" if p.get("threshold_met") else "") for p in fired[:5]))
    sig = [s for s in v.get("alive_signals") or [] if isinstance(s, dict)]
    lines.append(f"{t['alive']}: " + ("; ".join(_coded(lang, s.get("code")) + (f": {_cut(s.get('number'), 60)}" if s.get("number") else "") for s in sig[:3]) if sig else t["none"]))
    judge = _dict(os.path.join(run_dir, "judge.json"))
    changes = _dict(os.path.join(run_dir, "sheet-changes.json")).get("changes") or []
    agrees = t["agrees"] if judge.get("agrees") else t["disagrees"].format(v=judge.get("verdict_opinion"))
    lines.append(f"{t['judge']}: {agrees}; " + t["changes"].format(n=len(changes)))
    if v.get("need_label"):
        lines.append(f"{t['need']}: {v.get('need_label')}")
    return lines


def _report_lines(run_dir, lang):
    t = T[lang]
    v = _dict(os.path.join(run_dir, "verdict.json"))
    lines = [f"{t['report']}: {os.path.join(os.path.abspath(run_dir), 'report.md')}"]
    if v.get("riskiest_assumption"):
        lines.append(f"{t['risk']}: {_cut(v.get('riskiest_assumption'), 200)}")
    test = v.get("cheapest_test") or {}
    if isinstance(test, dict) and test.get("action"):
        lines.append(f"{t['test']}: {_cut(test.get('action'), 160)} → {_cut(test.get('threshold'), 140)}")
    if v.get("verdict") == "INSUFFICIENT_DATA":
        lines.append(t["collect"].format(n=len(v.get("to_collect") or [])))
    return lines


def _skip_lines(n, run, lang):
    t = T[lang]
    if n == 4 and run.get("early_exit") is not True:
        return [t["kill_skipped"]]
    return [t["early"]] if run.get("early_exit") is True else []


def build(run_dir, n, status, run, lang, state, now=None):
    now = now or time.time()
    head = _header(lang, n, status, run, now)
    if status == "skipped":
        body = _skip_lines(n, run, lang)
    else:
        rows = findings(run_dir)
        if n == 1:
            body = _card_lines(run_dir, run, lang)
        elif n == 2:
            body = _research_lines(run_dir, lang, rows)
        elif n == 3:
            body = _reconcile_lines(run_dir, run, lang, rows, state)
        elif n == 4:
            body = _kill_lines(run_dir, lang, rows)
        elif n == 5:
            body = _audit_lines(run_dir, lang)
        elif n == 6:
            body = _verdict_lines(run_dir, lang)
        else:
            body = _report_lines(run_dir, lang)
    return "\n".join([head] + [line for line in body if line])


def lang_code(name):
    s = str(name or "").strip().lower()
    if s.startswith(("ukr", "укр")) or s in ("uk", "ua", "uk-ua"):
        return "uk"
    return "en"


def detect_language(transcript_path, env=None):
    env = os.environ if env is None else env
    found = None
    if transcript_path:
        try:
            with open(transcript_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "OUTPUT_LANGUAGE" not in line:
                        continue
                    for m in LANG_RE.finditer(line):
                        value = m.group(1).strip()
                        if value.lower() in ("name", "<name>", "..."):
                            continue
                        found = value
        except OSError:
            pass
    if found:
        return found
    opt = env.get("CLAUDE_PLUGIN_OPTION_OUTPUT_LANGUAGE", "").strip()
    if opt and "${" not in opt:
        return opt
    return "English"


def candidate_runs(cwd, now=None, extra=()):
    now = now or time.time()
    pinned = os.environ.get(RUN_DIR_ENV)
    if pinned:
        headers = [os.path.join(pinned, "run.json")]
    else:
        headers = []
        for base in (os.path.join(cwd, "runs"), os.path.join(os.path.expanduser("~"), ".idea-evaluator", "runs")):
            headers += glob.glob(os.path.join(base, "*", "run.json")) + glob.glob(os.path.join(base, "*", "*", "run.json"))
        headers += [os.path.join(d, "run.json") for d in extra if os.path.isfile(os.path.join(d, "run.json"))]
        headers = list(dict.fromkeys(os.path.abspath(h) for h in headers))
    found = []
    for header in headers:
        parts = header.split(os.sep)
        if len(parts) >= 3 and (parts[-2] == "pivot" or parts[-3] == "branches"):
            continue
        try:
            age = now - os.path.getmtime(header)
        except OSError:
            continue
        if age > MAX_AGE_SECONDS:
            continue
        run = _load(header)
        if not isinstance(run, dict):
            continue
        run_dir = os.path.dirname(header)
        status = run.get("status")
        if status == "running":
            found.append((run_dir, run))
        elif status == "done" and age <= DONE_GRACE_SECONDS and os.path.exists(os.path.join(run_dir, STATE_FILE)):
            found.append((run_dir, run))
    return found


def _read_state(run_dir, run):
    state = _dict(os.path.join(run_dir, STATE_FILE))
    key = [run.get("run_id"), run.get("started_at")]
    if state.get("key") != key:
        state = {"key": key, "announced": {}, "log": []}
    return state


def _write_state(run_dir, state):
    path = os.path.join(run_dir, STATE_FILE)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, path)


def advance(run_dir, run, payload, now=None):
    now = now or time.time()
    state = _read_state(run_dir, run)
    fresh = not state["announced"] and not state.get("seen")
    state["seen"] = True
    if not state.get("lang"):
        state["lang"] = detect_language(payload.get("transcript_path"))
    lang = lang_code(state["lang"])
    pending = []
    for n in range(1, TOTAL + 1):
        if str(n) in state["announced"]:
            continue
        status = stage_status(run_dir, n, run)
        if not status:
            break
        pending.append((n, status))
    messages = []
    if pending and fresh and len(pending) >= 2 and run.get("source_run"):
        last = pending[-1][0]
        messages.append(f"[idea-evaluator 1-{last}/{TOTAL}] {T[lang]['from_saved']}: {run.get('source_run')}")
        for n, status in pending:
            state["announced"][str(n)] = "saved"
        pending = []
    for n, status in pending:
        messages.append(build(run_dir, n, status, run, lang, state, now=now))
        state["announced"][str(n)] = status
        if n == 2:
            state["findings_after_pass1"] = len(findings(run_dir))
        state["log"].append({"stage": n, "status": status, "event": payload.get("hook_event_name"),
                             "tool": payload.get("tool_name"), "at": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    _write_state(run_dir, state)
    return messages


def _locked(run_dir, fn):
    if fcntl is None:
        return fn()
    with open(os.path.join(run_dir, LOCK_FILE), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return fn()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def decide(payload, now=None):
    if payload.get("hook_event_name") != "PostToolUse" or payload.get("agent_id"):
        return None
    cwd = payload.get("cwd") or os.getcwd()
    text = load_text(payload.get("transcript_path"))
    runs = candidate_runs(cwd, now=now, extra=run_dirs(text))
    if runs and text is not None:
        runs = [(d, r) for d, r in runs if mentions(d, text)]
    messages = []
    for run_dir, run in runs:
        out = _locked(run_dir, lambda: advance(run_dir, run, payload, now=now))
        if out and len(runs) > 1:
            out = [f"{os.path.basename(run_dir)}\n{m}" for m in out]
        messages += out
    if not messages:
        return None
    return {"systemMessage": "\n\n".join(messages)}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    try:
        out = decide(payload if isinstance(payload, dict) else {})
    except Exception:
        out = None
    if out:
        json.dump(out, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
