"""Does the 'file it, don't bin it' behaviour actually happen?

The article claims a bulky tool result is replaced in the conversation by a short
preview plus a reference, with the full thing kept in storage and reachable via
retrieve_offloaded_content. Test: read a deliberately huge file with offloading on,
then look at what actually ended up in the conversation.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness

BIG = pathlib.Path(__file__).parent / ".big_file.txt"
NEEDLE = "CANARY-7f3a9b-END-OF-FILE"


def make_big(kb=400):
    lines = [f"{i:06d} routine log line with filler text to take up space, trace={i*7919:012x}"
             for i in range(kb * 1024 // 80)]
    lines.append(NEEDLE)
    BIG.write_text("\n".join(lines))
    return BIG.stat().st_size


def probe(label, **kw):
    agent = create_harness(model=MODEL, effort="off", builtin_tools=["read"],
                           memory=False, session=False, skills=False,
                           builtin_plugins=[], **kw)
    assert_haiku(agent)
    print(f"\n=== {label} ===")
    print(f"tools: {sorted(agent.tool_names)}")
    agent(f"Read the file {BIG} and tell me how many lines it has, roughly.")
    convo = json.dumps(agent.messages, default=str)
    return {
        "label": label,
        "tools": sorted(agent.tool_names),
        "has_retrieval_tool": "retrieve_offloaded_content" in agent.tool_names,
        "conversation_chars": len(convo),
        "full_content_in_conversation": NEEDLE in convo,
        "mentions_offload": any(w in convo.lower() for w in
                                ("offload", "truncated", "reference", "retrieve_offloaded")),
    }


if __name__ == "__main__":
    size = make_big()
    print(f"built {BIG.name}: {size:,} bytes (~{size//4:,} tokens if read whole)")
    out = []
    for label, kw in [("offloading ON (default)", {}),
                      ("offloading OFF", {"context_manager": False})]:
        try:
            out.append(probe(label, **kw))
        except Exception as e:
            out.append({"label": label, "ERROR": f"{type(e).__name__}: {e}"[:300]})
        print(json.dumps(out[-1], indent=2))
    pathlib.Path(__file__).with_name("results_offloading.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 74)
    for r in out:
        if "ERROR" in r:
            print(f"{r['label']:<26} ERROR: {r['ERROR'][:60]}")
            continue
        print(f"{r['label']:<26} convo={r['conversation_chars']:>9,} chars   "
              f"full file in convo: {str(r['full_content_in_conversation']):<6} "
              f"retrieval tool: {r['has_retrieval_tool']}")
    print("=" * 74)
    BIG.unlink(missing_ok=True)
