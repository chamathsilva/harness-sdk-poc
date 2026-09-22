"""Does delegating to a subagent really keep the work off the parent's desk?

The article claims a subagent does its reading on *its* desk, returning only a
conclusion. That is testable: give the parent a task over bulky files, have it
delegate, then look at what ended up in the parent's own conversation.

Each large record carries unique `trace_id=` strings. If those appear in the parent's
history, the file contents landed on the parent's desk after all.
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
import importlib
econ = importlib.import_module("02_context_economics")

D = econ.DATASETS["large"]
FILES = sorted(f.name for f in D.glob("*.json"))
TASK = (f"Delegate this entire job to a subagent, then report only what it tells you. "
        f"The subagent should read all {len(FILES)} JSON files in {D} "
        f"({FILES[0]} through {FILES[-1]}), total the 'downtime_minutes' per 'service', "
        "and return the totals sorted descending. Use absolute paths.")


def conversation_size(agent):
    return len(json.dumps(agent.messages, default=str))


def run(label, tools, task):
    agent = create_harness(model=MODEL, effort="off", builtin_tools=tools,
                           memory=False, session=False, skills=False,
                           builtin_plugins=[], context_manager=False)
    assert_haiku(agent)
    result = agent(task)
    convo = json.dumps(agent.messages, default=str)
    traces = len(set(re.findall(r"trace_id=([0-9a-f]{16})", convo)))
    u = result.metrics.accumulated_usage
    return {"label": label, "tools": tools,
            "parent_conversation_chars": len(convo),
            "distinct_trace_ids_in_parent": traces,
            "tool_calls": {k: v.call_count for k, v in result.metrics.tool_metrics.items()},
            "billable_input": u["inputTokens"] + u.get("cacheReadInputTokens", 0)
                              + u.get("cacheWriteInputTokens", 0),
            "answer_tail": str(result)[-300:]}


if __name__ == "__main__":
    out = []
    for label, tools, task in [
        ("delegated to subagent", ["read", "subagent"], TASK),
        ("did it itself",         ["read"],             econ.build_task(D)),
    ]:
        print(f"\n=== {label} ===", flush=True)
        try:
            r = run(label, tools, task)
        except Exception as e:
            r = {"label": label, "ERROR": f"{type(e).__name__}: {e}"}
        print(json.dumps({k: v for k, v in r.items() if k != "answer_tail"}, indent=2), flush=True)
        out.append(r)
    pathlib.Path(__file__).with_name("results_subagent.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 70)
    for r in out:
        if "ERROR" in r: continue
        print(f"{r['label']:<24} parent convo: {r['parent_conversation_chars']:>8,} chars   "
              f"trace_ids leaked into parent: {r['distinct_trace_ids_in_parent']:>4}")
    print("=" * 70)
