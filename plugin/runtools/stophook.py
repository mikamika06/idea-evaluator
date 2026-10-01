import glob
import json
import os
import re
import sys
import time

from runtools.rule import RULES_VERSION
from runtools.runcheck import check
from runtools.session import load_text, mentions, run_dirs

MAX_BLOCKS = 6
MAX_AGE_SECONDS = 12 * 3600
RUN_DIR_ENV = "IDEA_EVALUATOR_RUN_DIR"
LAUNCH_RES = (
    re.compile(r"Async agent launched successfully.*?agentId: ([A-Za-z0-9_-]+)", re.S),
    re.compile(r"Command running in background with ID: ([A-Za-z0-9_-]+)"),
)
NOTICE_RE = re.compile(r"<task-notification>\s*<task-id>([^<\s]+)</task-id>")


def _version(value):
    m = re.fullmatch(r"v(\d+)", str(value or ""))
    return int(m.group(1)) if m else None


def supported(value):
    n = _version(value)
    return n is not None and 1 <= n <= _version(RULES_VERSION)


def active_runs(cwd, now=None, extra=()):
    now = now or time.time()
    found = []
    pinned = os.environ.get(RUN_DIR_ENV)
    if pinned:
        headers = [os.path.join(pinned, "run.json")]
    else:
        headers = []
        for base in (os.path.join(cwd, "runs"), os.path.join(os.path.expanduser("~"), ".idea-evaluator", "runs")):
            headers += glob.glob(os.path.join(base, "*", "run.json")) + glob.glob(os.path.join(base, "*", "*", "run.json"))
        headers += [os.path.join(d, "run.json") for d in extra if os.path.isfile(os.path.join(d, "run.json"))]
        headers = list(dict.fromkeys(os.path.abspath(h) for h in headers))
    for header in headers:
        try:
            with open(header) as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if data.get("status") != "running" or not supported(data.get("rules_version")) or data.get("awaiting"):
            continue
        if now - os.path.getmtime(header) > MAX_AGE_SECONDS:
            continue
        found.append(os.path.dirname(header))
    return found


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def _tool_results(record):
    message = record.get("message") if isinstance(record, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return
    for part in content:
        if isinstance(part, dict) and part.get("type") == "tool_result":
            yield from _strings(part.get("content"))


def read_transcript(path):
    text = load_text(path)
    if text is None:
        return None
    launched = []
    finished = set()
    for line in text.splitlines():
        if "task-notification" not in line and "launched successfully" not in line and "running in background" not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        for item in _tool_results(record):
            for pattern in LAUNCH_RES:
                launched += pattern.findall(item)
        for item in _strings(record):
            finished.update(NOTICE_RE.findall(item))
    return {"pending": [t for t in dict.fromkeys(launched) if t not in finished], "text": text}


def decide(payload, now=None):
    cwd = payload.get("cwd") or os.getcwd()
    transcript = read_transcript(payload.get("transcript_path"))
    if transcript and transcript["pending"]:
        return None
    reasons = []
    extra = run_dirs(transcript["text"]) if transcript else []
    for run_dir in active_runs(cwd, now=now, extra=extra):
        if transcript and not mentions(run_dir, transcript["text"]):
            continue
        counter = os.path.join(run_dir, ".stop-blocks")
        try:
            with open(counter) as f:
                blocks = int(f.read().strip() or 0)
        except (OSError, ValueError):
            blocks = 0
        if blocks >= MAX_BLOCKS:
            continue
        result = check(run_dir)
        if result["ok"]:
            continue
        with open(counter, "w") as f:
            f.write(str(blocks + 1))
        parts = []
        if result["missing"]:
            parts.append("missing " + ", ".join(result["missing"]))
        if result["errors"]:
            parts.append("errors: " + "; ".join(result["errors"]))
        reasons.append(f"Evaluation run {run_dir} is not complete (next stage: {result['next_stage'] or 'fix errors'}): " + " | ".join(parts) + ". Continue the evaluate skill from that stage, then set run.json status to done.")
    if not reasons:
        return None
    return {"decision": "block", "reason": "\n".join(reasons)}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    out = decide(payload)
    if out:
        json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
