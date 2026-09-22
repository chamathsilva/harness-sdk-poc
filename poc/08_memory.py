"""Does long-term memory actually survive into a brand-new conversation?

The article claims facts learned in one conversation come back in later ones, stored
as editable markdown. Testing it end to end: teach agent #1 something arbitrary that
cannot be guessed, flush, then build a completely separate agent over the same memory
directory and ask.
"""
import asyncio, json, pathlib, shutil, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness

MEM = pathlib.Path(__file__).parent / ".memory_test"
# Arbitrary and unguessable, so a correct answer cannot be a lucky prior.
FACT = "Our deploy freeze codeword is 'juniper-thicket' and it is owned by the Raft team."
PROBE = "What is our deploy freeze codeword, and which team owns it?"


def build(**kw):
    a = create_harness(model=MODEL, effort="off", builtin_tools=[],
                       memory={"dir": str(MEM)}, session=False, skills=False,
                       builtin_plugins=[], context_manager=False, **kw)
    assert_haiku(a)
    return a


async def main():
    if MEM.exists():
        shutil.rmtree(MEM)

    print("=== conversation 1: teaching it the fact ===")
    a1 = build()
    a1(f"Remember this for later: {FACT}")
    if a1.memory_manager:
        await a1.memory_manager.flush()

    files = sorted(p for p in MEM.rglob("*") if p.is_file()) if MEM.exists() else []
    print(f"\nmemory dir: {MEM}")
    print(f"files written: {[str(p.relative_to(MEM)) for p in files] or 'NONE'}")
    stored = "\n".join(p.read_text() for p in files if p.suffix in (".md", ".txt", ".json"))
    print(f"\n--- stored content ({len(stored)} chars) ---\n{stored[:700]}")

    print("\n=== conversation 2: a brand-new agent, same memory dir ===")
    a2 = build()
    print(f"(fresh agent, {len(a2.messages)} prior messages in its history)")
    answer = str(a2(PROBE))

    recalled = "juniper" in answer.lower()
    team = "raft" in answer.lower()
    print("\n" + "=" * 70)
    print(f"codeword recalled : {recalled}")
    print(f"owning team recalled: {team}")
    print(f"VERDICT: {'MEMORY PERSISTED ACROSS CONVERSATIONS' if recalled else 'NOT RECALLED'}")
    print("=" * 70)

    pathlib.Path(__file__).with_name("results_memory.json").write_text(json.dumps({
        "memory_files": [str(p.relative_to(MEM)) for p in files],
        "stored_chars": len(stored), "stored_excerpt": stored[:1500],
        "recalled_codeword": recalled, "recalled_team": team,
        "answer": answer[-600:],
    }, indent=2))


asyncio.run(main())
