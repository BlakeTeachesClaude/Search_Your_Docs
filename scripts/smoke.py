#!/usr/bin/env python3
"""Smoke suite with a GO / CONDITIONAL GO / NO-GO report.

Run before teaching a session:  python scripts/smoke.py
Writes reports/smoke-report.md and reports/smoke-report.json. Exit 0 = GO or CONDITIONAL GO, 1 = NO-GO.
--strict treats CONDITIONAL GO as NO-GO.  --live adds a real Claude API call (needs ANTHROPIC_API_KEY + ANTHROPIC_MODEL).
Statuses: PASS, FAIL, WARN (non-blocking issue), SKIP (not exercised).
A failed *required* check is NO-GO; a failed optional check, a WARN, or a SKIP of a live check is CONDITIONAL GO.
"""
import datetime as dt
import importlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = []


def check(name, required=True):
    def deco(fn):
        t = time.time()
        try:
            status, detail = fn()
        except Exception as exc:  # a crashing check is a failing check
            status, detail = "FAIL", f"{type(exc).__name__}: {exc}"
        if status == "FAIL" and not required:
            status = "WARN"
        RESULTS.append({"name": name, "required": required, "status": status,
                        "detail": detail, "seconds": round(time.time() - t, 2)})
        return fn
    return deco


def run_checks(live):
    @check("Python 3.10+")
    def _():
        ok = sys.version_info >= (3, 10)
        return ("PASS" if ok else "FAIL"), platform.python_version()

    @check("scikit-learn installed")
    def _():
        import sklearn
        return "PASS", sklearn.__version__

    @check("anthropic SDK installed (needed for --answer)", required=False)
    def _():
        import anthropic
        return "PASS", getattr(anthropic, "__version__", "unknown")

    @check("fixture documents present")
    def _():
        names = sorted(p.name for p in (ROOT / "documents").glob("*.md"))
        return ("PASS" if names == ["leave.md", "security.md", "travel.md"] else "FAIL"), ", ".join(names)

    @check("index builds from fixtures")
    def _():
        import rag
        chunks = rag.load_chunks(ROOT / "documents")
        rag.build_index(chunks)
        return "PASS", f"{len(chunks)} chunks"

    @check("reference solution (rag.py): in-domain question cites travel.md#1 and $180")
    def _():
        out = subprocess.run([sys.executable, str(ROOT / "rag.py"), "What is the hotel reimbursement limit?"],
                             capture_output=True, text=True, timeout=60)
        ok = out.returncode == 0 and "[travel.md#1]" in out.stdout and "$180" in out.stdout
        return ("PASS" if ok else "FAIL"), (out.stderr.strip() or "retrieval output ok")

    @check("reference solution (rag.py): unsupported question returns no evidence")
    def _():
        out = subprocess.run([sys.executable, str(ROOT / "rag.py"), "Who won the 1980 Olympics?"],
                             capture_output=True, text=True, timeout=60)
        ok = out.returncode == 0 and "No matching evidence found." in out.stdout
        return ("PASS" if ok else "FAIL"), "refuses without evidence"

    # ---- the learner's actual path: environment -> documents -> code along (uses the code shown on the slides) ----
    import shutil
    import tempfile
    sys.path.insert(0, str(ROOT / "scripts"))
    import lab_journey as journey
    tmp = Path(tempfile.mkdtemp(prefix="rag-smoke-"))

    @check("learner: new_workspace.py builds workspace + environment check passes")
    def _():
        ws = tmp / "ws0"
        r = journey.new_workspace(ws)
        if r.returncode != 0:
            return "FAIL", r.stderr.strip()
        c = journey.run(ws, "check.py", "0")
        docs = len(list((ws / "documents").glob("*.md")))
        return ("PASS" if c.returncode == 0 and docs == 3 else "FAIL"), (f"{docs} documents; " + c.stdout.strip().splitlines()[-1])

    @check("learner: starter file fails with a clear hint (checks are not vacuous)")
    def _():
        ws = tmp / "ws1"
        journey.new_workspace(ws)
        run = journey.run(ws, "my_rag.py")
        chk = journey.run(ws, "check.py", "1")
        ok = run.returncode != 0 and "write load_chunks" in run.stderr and chk.returncode == 1 and "hint" in chk.stdout
        return ("PASS" if ok else "FAIL"), "stubs raise NotImplementedError; check.py 1 fails with a hint"

    for step in (1, 2, 3, 4):
        @check(f"learner: typing slide code for steps 1-{step} passes check.py {step}" + (" and my_rag.py runs" if step < 4 else ""))
        def _(step=step):
            ws = tmp / f"ws_step{step}"
            journey.new_workspace(ws)
            journey.type_steps(ws, step)
            chk = journey.run(ws, "check.py", str(step))
            if chk.returncode != 0:
                return "FAIL", chk.stdout.strip().splitlines()[-3:].__str__()
            if step < 4:
                run = journey.run(ws, "my_rag.py")
                if run.returncode != 0:
                    return "FAIL", run.stderr.strip()[-200:]
            return "PASS", chk.stdout.strip().splitlines()[-1]

    @check("learner: bring-your-own documents copies only safe .md/.txt files")
    def _():
        src = tmp / "mine"
        src.mkdir()
        (src / "a.md").write_text("alpha policy text", encoding="utf-8")
        (src / "notes.pdf").write_bytes(b"%PDF")
        (src / ".secret.md").write_text("hidden", encoding="utf-8")
        ws = tmp / "ws_custom"
        r = journey.new_workspace(ws, docs=src)
        got = sorted(p.name for p in (ws / "documents").rglob("*") if p.is_file())
        return ("PASS" if r.returncode == 0 and got == ["a.md"] else "FAIL"), f"copied {got}"

    if live:
        @check("LIVE: step 4 end to end with the real Claude API (my_rag.py)", required=False)
        def _():
            if not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("ANTHROPIC_MODEL")):
                return "SKIP", "no credentials"
            ws = tmp / "ws_live"
            journey.new_workspace(ws)
            journey.type_steps(ws, 4)
            r = journey.run(ws, "my_rag.py", timeout=180)
            ok = r.returncode == 0 and "travel.md#1" in r.stdout and "180" in r.stdout.split("answer:")[-1]
            return ("PASS" if ok else "FAIL"), (r.stderr.strip()[-150:] or r.stdout.strip().splitlines()[-1][:150])

    @check("Claude project config present (CLAUDE.md + .claude/settings.json)")
    def _():
        perms = json.loads((ROOT / ".claude" / "settings.json").read_text())["permissions"]
        ok = (ROOT / "CLAUDE.md").exists() and {"allow", "ask", "deny"} <= perms.keys()
        return ("PASS" if ok else "FAIL"), f"{len(perms['allow'])} allow / {len(perms['ask'])} ask / {len(perms['deny'])} deny"

    @check("HTML deck present, self-contained, opens from file://")
    def _():
        import re
        text = (ROOT / "deck" / "index.html").read_text(encoding="utf-8")
        slides = text.count('class="slide"')
        external = re.findall(r'(?:src|href)\s*=\s*["\']https?://[^"\']+', text)
        ok = slides >= 10 and not external
        return ("PASS" if ok else "FAIL"), f"{slides} slides, {len(external)} external references"

    @check("offline regression suite passes")
    def _():
        out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-m", "not live", "-x"],
                             capture_output=True, text=True, cwd=ROOT, timeout=300)
        tail = (out.stdout.strip().splitlines() or ["no output"])[-1]
        return ("PASS" if out.returncode == 0 else "FAIL"), tail

    @check("Claude API key + model configured", required=False)
    def _():
        have = bool(os.environ.get("ANTHROPIC_API_KEY")) , os.environ.get("ANTHROPIC_MODEL")
        if all(have):
            return "PASS", f"model={have[1]}"
        return "SKIP", "set ANTHROPIC_API_KEY and ANTHROPIC_MODEL to exercise --answer"

    if live:
        @check("LIVE: Claude answers with citation", required=False)
        def _():
            if not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("ANTHROPIC_MODEL")):
                return "SKIP", "no credentials"
            import rag
            chunks = rag.load_chunks(ROOT / "documents")
            vec, mat = rag.build_index(chunks)
            q = "What is the hotel reimbursement limit?"
            text = rag.answer(q, rag.retrieve(q, chunks, vec, mat))
            ok = "travel.md#1" in text and "180" in text
            return ("PASS" if ok else "FAIL"), text[:120].replace("\n", " ")

    @check("manual compatibility sign-offs current", required=False)
    def _():
        data = json.loads((ROOT / "compat" / "verified.json").read_text())
        limit, today, problems = data["max_age_days"], dt.date.today(), []
        for surface, info in data["surfaces"].items():
            if not info["last_verified"]:
                problems.append(f"{surface}: never verified")
                continue
            age = (today - dt.date.fromisoformat(info["last_verified"])).days
            if age > limit:
                problems.append(f"{surface}: {age} days old")
        return ("WARN", "; ".join(problems)) if problems else ("PASS", "all surfaces verified recently")


def verdict(strict):
    if any(r["status"] == "FAIL" and r["required"] for r in RESULTS):
        return "NO-GO"
    if any(r["status"] in {"FAIL", "WARN", "SKIP"} for r in RESULTS):
        return "NO-GO" if strict else "CONDITIONAL GO"
    return "GO"


def write_reports(v):
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    (out / "smoke-report.json").write_text(json.dumps({"verdict": v, "generated": stamp, "results": RESULTS}, indent=2))
    icon = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}
    lines = [f"# Smoke report: {v}", "", f"Generated {stamp} on {platform.system()} {platform.release()}", "",
             "| Status | Check | Required | Detail |", "|---|---|---|---|"]
    for r in RESULTS:
        lines.append(f"| {icon[r['status']]} | {r['name']} | {'yes' if r['required'] else 'no'} | {r['detail']} |")
    blockers = [r for r in RESULTS if r["status"] == "FAIL" and r["required"]]
    caveats = [r for r in RESULTS if r["status"] in {"FAIL", "WARN", "SKIP"} and r not in blockers]
    if blockers:
        lines += ["", "## Blockers (fix before teaching)"] + [f"- {r['name']}: {r['detail']}" for r in blockers]
    if caveats:
        lines += ["", "## Caveats (go, but know these)"] + [f"- {r['name']}: {r['detail']}" for r in caveats]
    (out / "smoke-report.md").write_text("\n".join(lines) + "\n")
    return out / "smoke-report.md"


def main():
    strict, live = "--strict" in sys.argv, "--live" in sys.argv
    run_checks(live)
    v = verdict(strict)
    path = write_reports(v)
    for r in RESULTS:
        print(f"[{r['status']:<4}] {r['name']} - {r['detail']}")
    print(f"\nVERDICT: {v}   (report: {path.relative_to(ROOT)})")
    sys.exit(1 if v == "NO-GO" else 0)


if __name__ == "__main__":
    main()
