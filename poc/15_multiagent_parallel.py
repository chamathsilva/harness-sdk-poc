"""Where a topology should win: genuine parallelism.

Experiment 14 found a single agent beat every topology on a sequential task. That is
the topology's worst case. This is its best case: three genuinely independent analyses
that a graph can run concurrently and a single agent must do one after another.

If fan-out parallelism does not win here, it is hard to see where it would.

  single  one agent does all three analyses in sequence, then synthesises
  graph   splitter -> [by_service, by_cause, by_severity] -> synthesis
"""
import json, pathlib, statistics, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
from strands.multiagent import GraphBuilder
import importlib
econ = importlib.import_module("02_context_economics")

D = econ.DATASETS["large"]          # bulky, so each branch does real work
FILES = sorted(f.name for f in D.glob("*.json"))
TOOLS = ["read", "programmatic_tool_caller"]

DATA = (f"The directory {D} holds {len(FILES)} JSON incident records "
        f"({FILES[0]} to {FILES[-1]}). Each has 'service', 'downtime_minutes', "
        "'severity', 'root_cause' and a long 'log_tail'.")

ANALYSES = {
    "by_service":  "total downtime minutes per service, sorted descending",
    "by_cause":    "the number of incidents per root_cause, sorted descending",
    "by_severity": "the number of incidents per severity level, sorted descending",
}

SINGLE = (DATA + "\n\nProduce all three of these analyses:\n"
          + "\n".join(f"{i+1}. {d}" for i, d in enumerate(ANALYSES.values()))
          + "\n\nThen give a one-sentence summary. Use exact numbers.")


def mk(name, desc, instructions, tools=TOOLS):
    a = create_harness(model=MODEL, effort="off", builtin_tools=tools,
                       instructions=instructions, memory=False, session=False,
                       skills=False, builtin_plugins=[], context_manager=False,
                       name=name, description=desc)
    assert_haiku(a)
    return a


def build_graph():
    b = GraphBuilder()
    b.add_node(mk("splitter", "hands the job to three analysts",
                  "Restate the task for the analysts in one short line. Do not do the analysis.",
                  tools=[]), "splitter")
    # The join node must exist before any edge points at it.
    b.add_node(mk("synthesis", "combines the three analyses",
                  "You are given three analyses. Restate all three verbatim with their exact "
                  "numbers, then add one sentence of summary.", tools=[]), "synthesis")
    for key, desc in ANALYSES.items():
        b.add_node(mk(key, f"computes {desc}",
                      f"Using programmatic_tool_caller, compute {desc}. "
                      "Report only that result, with exact numbers."), key)
        b.add_edge("splitter", key)
        b.add_edge(key, "synthesis")
    b.set_entry_point("splitter")
    b.set_max_node_executions(10)
    return b.build()


def usage_of(o):
    u = getattr(o, "accumulated_usage", None) or {}
    return (u.get("inputTokens", 0) + u.get("cacheReadInputTokens", 0)
            + u.get("cacheWriteInputTokens", 0)), u.get("outputTokens", 0)


def grade(text):
    truth = econ.ground_truth(D)
    return {"service_figures": sum(1 for v in truth.values() if str(v) in text),
            "of": len(truth),
            "covers_all_three": all(w in text.lower() for w in
                                    ("service", "cause", "sev"))}


def run(arch):
    t0 = time.time()
    if arch == "single":
        r = mk("solo", "does all three", "")(SINGLE)
        bill, out = usage_of(r.metrics)
        extra = {"tool_calls": {k: v.call_count for k, v in r.metrics.tool_metrics.items()}}
    else:
        g = build_graph()
        r = g(SINGLE)
        bill, out = usage_of(r)
        extra = {"execution_order": [getattr(n, "node_id", str(n)) for n in r.execution_order],
                 "status": str(r.status),
                 "node_times": {k: round(getattr(v, "execution_time", 0) / 1000, 1)
                                for k, v in (r.results or {}).items()}}
    dt = time.time() - t0
    return {"arch": arch, "seconds": round(dt, 1), "billable_input": bill,
            "output_tokens": out, **grade(str(r)), **extra, "answer_tail": str(r)[-400:]}


if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    rows = []
    for arch in ("single", "graph"):
        for i in range(trials):
            print(f"[{arch}] trial {i+1}/{trials}", flush=True)
            try:
                rows.append(run(arch) | {"trial": i + 1})
            except Exception as e:
                rows.append({"arch": arch, "trial": i + 1, "ERROR": f"{type(e).__name__}: {e}"[:300]})
    pathlib.Path(__file__).with_name("results_multiagent_parallel.json").write_text(json.dumps(rows, indent=2))

    print(f"\n{'='*76}\nTHREE INDEPENDENT ANALYSES (the topology's best case)\n{'='*76}")
    print(f"{'arch':<9}{'wall sec':>10}{'billable_in':>14}{'out':>8}{'svc figs':>10}{'all 3':>8}")
    print("-" * 76)
    for arch in ("single", "graph"):
        v = [r for r in rows if r.get("arch") == arch and "ERROR" not in r]
        if not v:
            print(f"{arch:<9}  FAILED: {next((r['ERROR'][:50] for r in rows if r.get('arch')==arch), '?')}")
            continue
        print(f"{arch:<9}{statistics.median(r['seconds'] for r in v):>10.1f}"
              f"{statistics.median(r['billable_input'] for r in v):>14,.0f}"
              f"{statistics.median(r['output_tokens'] for r in v):>8,.0f}"
              f"{statistics.mean(r['service_figures'] for r in v):>9.1f}/6"
              f"{sum(r['covers_all_three'] for r in v):>6}/{len(v)}")
    g = [r for r in rows if r.get("arch") == "graph" and "node_times" in r]
    if g:
        print(f"\nper-node seconds (trial 1): {g[0]['node_times']}")
        print(f"execution order: {g[0]['execution_order']}")
