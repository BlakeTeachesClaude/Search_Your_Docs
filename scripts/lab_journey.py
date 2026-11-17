"""Shared by smoke.py and the tests: replays what a learner does, using the exact code shown on the slides."""
import re
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = re.compile(r"(?m)^# STEP (\d): .*$")


def slide_code():
    """The four code blocks learners type, taken from the deck so slides and checks cannot drift apart."""
    slides = runpy.run_path(str(ROOT / "scripts" / "build_deck.py"))["SLIDES"]
    blocks = [s["code"] for s in slides if s["type"] == "code" and s.get("step")]
    assert len(blocks) == 4, f"expected 4 step code slides, found {len(blocks)}"
    return blocks


def new_workspace(ws, docs=None):
    cmd = [sys.executable, str(ROOT / "scripts" / "new_workspace.py"), "--dir", str(ws)]
    if docs:
        cmd += ["--docs", str(docs)]
    return subprocess.run(cmd, capture_output=True, text=True)


def type_steps(ws, upto):
    """Replace the first `upto` stubs in ws/my_rag.py with the slide code and set STEP, like a learner would."""
    path = Path(ws) / "my_rag.py"
    text = path.read_text(encoding="utf-8")
    blocks = slide_code()
    marks = list(MARK.finditer(text))
    end = text.index("\ndef main():")
    out, last = [text[: marks[0].start()]], None
    for k, m in enumerate(marks):
        stop = marks[k + 1].start() if k + 1 < len(marks) else end
        header = m.group(0)
        out.append(header + "\n" + blocks[k].rstrip() + "\n\n\n" if k < upto else text[m.start():stop])
    out.append(text[end:])
    new = "".join(out)
    new = re.sub(r"(?m)^STEP = \d+", f"STEP = {upto}", new)
    path.write_text(new, encoding="utf-8")


def run(ws, *args, env=None, timeout=120):
    return subprocess.run([sys.executable, *args], cwd=ws, capture_output=True, text=True, env=env, timeout=timeout)
