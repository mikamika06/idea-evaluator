import os
import shutil
import subprocess
import sys


def _configured():
    for name in ("settings.json", "settings.local.json"):
        try:
            with open(os.path.join(os.path.expanduser("~"), ".claude", name), encoding="utf-8") as f:
                if "rtk hook" in f.read():
                    return True
        except OSError:
            continue
    return False


def plan(which=shutil.which):
    rtk = which("rtk")
    if not rtk or _configured():
        return None
    return [rtk, "hook", "claude"]


def main():
    cmd = plan()
    payload = sys.stdin.read()
    if not cmd:
        return 0
    try:
        proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    sys.stdout.write(proc.stdout)
    return 0
