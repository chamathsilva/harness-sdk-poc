"""Does a session really survive a process restart, not just a new agent object?

Experiment 08 proved long-term *memory* crosses conversations. This is the different
claim: that a conversation is saved to disk and resumable by id. Testing it properly
means a second OS process, not a second object in the same interpreter -- otherwise
anything cached in memory could carry the answer.

Run with no argument to drive both phases as subprocesses.
"""
import json, pathlib, shutil, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

HERE = pathlib.Path(__file__).resolve().parent
SESSIONS = HERE / ".session_test"
SID = "restart-probe-1"
# Arbitrary, unguessable, and never repeated in phase two's prompt.
FACT = "The incident bridge number is 555-0142 and the escalation owner is Priya."


def agent():
    from _env import load, assert_haiku, MODEL
    load()
    from strands_harness import create_harness
    a = create_harness(model=MODEL, effort="off", builtin_tools=[],
                       session={"id": SID, "dir": str(SESSIONS)},
                       memory=False, skills=False, builtin_plugins=[],
                       context_manager=False)
    assert_haiku(a)
    return a


# Results go to files, not stdout: the agent streams its reply to stdout, so a
# result line printed there gets interleaved and is unreliable to parse back.
OUT1 = HERE / ".phase1.json"
OUT2 = HERE / ".phase2.json"


def phase_one():
    a = agent()
    a(f"Please note this for our call: {FACT}")
    OUT1.write_text(json.dumps({"phase": 1, "messages": len(a.messages),
                                "session_id": a.session_id}))


def phase_two():
    a = agent()
    prior = len(a.messages)
    ans = str(a("What is the incident bridge number, and who is the escalation owner?"))
    OUT2.write_text(json.dumps({"phase": 2, "messages_restored_before_asking": prior,
                                "recalled_number": "555-0142" in ans,
                                "recalled_owner": "priya" in ans.lower(),
                                "answer": ans[-300:]}))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        {"one": phase_one, "two": phase_two}[sys.argv[1]]()
    else:
        if SESSIONS.exists():
            shutil.rmtree(SESSIONS)
        OUT1.unlink(missing_ok=True)
        OUT2.unlink(missing_ok=True)
        py = str(HERE.parent / ".venv" / "bin" / "python")
        out = {}
        for phase, dest in (("one", OUT1), ("two", OUT2)):
            print(f"=== launching process for phase {phase} ===", flush=True)
            p = subprocess.run([py, __file__, phase], capture_output=True, text=True, cwd=HERE)
            if not dest.exists():
                print(f"  phase {phase} wrote no result. stderr tail:\n{p.stderr[-800:]}")
                out[phase] = {"ERROR": "no result file"}
                continue
            out[phase] = json.loads(dest.read_text())
            print(json.dumps(out[phase], indent=2))

        files = sorted(p for p in SESSIONS.rglob("*") if p.is_file()) if SESSIONS.exists() else []
        print(f"\nsession files on disk: {len(files)}")
        (HERE / "results_session_restart.json").write_text(json.dumps(
            {"phases": out, "session_files": len(files),
             "sample_paths": [str(f.relative_to(SESSIONS)) for f in files[:5]]}, indent=2))
        two = out.get("two", {})
        print("\n" + "=" * 70)
        print(f"history restored in new process : {two.get('messages_restored_before_asking')} messages")
        print(f"recalled the number             : {two.get('recalled_number')}")
        print(f"recalled the owner              : {two.get('recalled_owner')}")
        print(f"VERDICT: {'SESSION SURVIVED PROCESS RESTART' if two.get('recalled_number') else 'NOT RECALLED'}")
        print("=" * 70)
        shutil.rmtree(SESSIONS, ignore_errors=True)
        OUT1.unlink(missing_ok=True)
        OUT2.unlink(missing_ok=True)
