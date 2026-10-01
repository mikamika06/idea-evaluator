import json
import os
import re

RUN_DIR_RE = re.compile(r"RUN_DIR:[ \t]*([~/][^\s\"'`\\<>|,;)]*)")


def load_text(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return None


def mentions(run_dir, text):
    candidates = {run_dir, os.path.realpath(run_dir)}
    home = os.path.expanduser("~")
    for c in list(candidates):
        if c.startswith(home + os.sep):
            candidates.add("~" + c[len(home):])
    return any(c in text or json.dumps(c)[1:-1] in text for c in candidates)


def run_dirs(text):
    if not text:
        return []
    found = []
    for raw in RUN_DIR_RE.findall(text):
        path = os.path.normpath(os.path.expanduser(raw.rstrip(".")))
        if os.path.isabs(path) and path not in found:
            found.append(path)
    return found
