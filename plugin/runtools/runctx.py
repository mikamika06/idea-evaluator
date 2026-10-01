import json
import os

from runtools.support import load_checks


def _load(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load_context(run_dir, with_judge=True):
    q3 = _load(os.path.join(run_dir, "q3.json"))
    if not (isinstance(q3, dict) and "invisible_player_risk" in q3):
        comp = _load(os.path.join(run_dir, "q3-competitors.json"))
        if isinstance(comp, dict):
            q3 = {**(q3 or {}), "invisible_player_risk": comp.get("invisible_player_risk")}
    return {
        "run": _load(os.path.join(run_dir, "run.json")),
        "support": load_checks(run_dir),
        "audit": _load(os.path.join(run_dir, "audit.json")),
        "judge": _load(os.path.join(run_dir, "judge.json")) if with_judge else None,
        "killcheck": _load(os.path.join(run_dir, "killcheck.json")),
        "law": _load(os.path.join(run_dir, "law.json")),
        "q3": q3,
    }
