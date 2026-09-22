"""When does a multi-agent topology actually beat one agent?

Four architectures, same task, same model, same data:

  single    one harness agent does everything
  subagent  one harness agent that may delegate (the harness's built-in delegation)
  graph     a deterministic pipeline: extract -> analyse -> write
  swarm     three specialists that hand off to each other autonomously

Every arm gets `read` and `programmatic_tool_caller`, so arithmetic is done by code in
all of them. That isolates architecture as the variable rather than re-measuring the
accuracy gap from experiment 04.

Two tasks: a three-stage analysis where structure plausibly helps, and a trivial
question where any topology is pure overhead.
"""
import json, pathlib, re, statistics, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
from strands.multiagent import GraphBuilder, Swarm
import importlib
econ = importlib.import_module("02_context_economics")

D = econ.DATASETS["small"]
FILES = sorted(f.name for f in D.glob("*.json"))
TRUTH = econ.ground_truth(D)
WORST = max(TRUTH, key=TRUTH.get)
TOOLS = ["read", "programmatic_tool_caller"]

COMPLEX = (
    f"The directory {D} holds {len(FILES)} JSON incident records ({FILES[0]} to {FILES[-1]}), "
    "each with 'service', 'downtime_minutes' and 'root_cause'.\n"
    "Do three things, in order:\n"
    "1. Total the downtime minutes per service, sorted descending. Exact numbers.\n"
    "2. Name the worst service and its most common root cause.\n"
    "3. Write two sentences of remediation advice for that service.\n"
    "Your final answer must contain all three."
)
TRIVIAL = "What is 17 multiplied by 23? Answer with just the number."


def mk(name, desc, instructions, tools=TOOLS):
    a = create_harness(model=MODEL, effort="off", builtin_tools=tools,
                       instructions=instructions, memory=False, session=False,
                       skills=False, builtin_plugins=[], context_manager=False,
                       name=name, description=desc)
    assert_haiku(a)
    return a


def build_graph():
    b = GraphBuilder()
    b.add_node(mk("extractor", "Reads incident files and totals downtime per service",
                  "You read the incident files and compute exact totals per service. "
                  "Use programmatic_tool_caller. Output the totals and each service's root causes."), "extractor")
    b.add_node(mk("analyst", "Finds the worst service and its dominant root cause",
                  "Given totals and root causes, name the worst service and its most common "
                  "root cause. Restate the totals you were given, exactly.", tools=[]), "analyst")
    b.add_node(mk("writer", "Writes remediation advice",
                  "Given an analysis, restate the totals and the worst service verbatim, then add "
                  "exactly two sentences of remediation advice.", tools=[]), "writer")
    b.add_edge("extractor", "analyst")
    b.add_edge("analyst", "writer")
    b.set_entry_point("extractor")
    b.set_max_node_executions(6)
    return b.build()


def build_swarm():
    e = mk("extractor", "Reads incident files and totals downtime per service",
           "You read incident files and compute exact totals per service using "
           "programmatic_tool_caller. When done, hand off to the analyst.")
    a = mk("analyst", "Finds the worst service and its dominant root cause",
           "Given totals, name the worst service and its most common root cause, "
           "restate the totals exactly, then hand off to the writer.", tools=[])
    w = mk("writer", "Writes remediation advice",
           "Restate the totals and worst service verbatim, then add exactly two "
           "sentences of remediation advice. Then stop.", tools=[])
    return Swarm([e, a, w], entry_point=e, max_handoffs=6, max_iterations=6)


def grade(task, text):
    if task == "trivial":
        return {"correct": "391" in text}
    figs = sum(1 for v in TRUTH.values() if str(v) in text)
    return {"exact_figures": figs, "of": len(TRUTH),
            "named_worst": WORST in text.lower(),
            "has_advice": len(text) > 400}


def usage_of(obj):
    u = getattr(obj, "accumulated_usage", None) or {}
    return (u.get("inputTokens", 0) + u.get("cacheReadInputTokens", 0)
            + u.get("cacheWriteInputTokens", 0)), u.get("outputTokens", 0)


def run(arch, task_name, prompt):
    t0 = time.time()
    if arch == "single":
        agent = mk("solo", "does the whole job", "")
        r = agent(prompt)
        bill, out = usage_of(r.metrics)
        extra = {"tool_calls": {k: v.call_count for k, v in r.metrics.tool_metrics.items()}}
    elif arch == "subagent":
        agent = mk("lead", "may delegate", "", tools=TOOLS + ["subagent"])
        r = agent(prompt)
        bill, out = usage_of(r.metrics)
        extra = {"tool_calls": {k: v.call_count for k, v in r.metrics.tool_metrics.items()}}
    elif arch == "graph":
        r = build_graph()(prompt)
        bill, out = usage_of(r)
        extra = {"execution_order": [getattr(n, "node_id", str(n)) for n in r.execution_order],
                 "status": str(r.status)}
    else:
        r = build_swarm()(prompt)
        bill, out = usage_of(r)
        extra = {"node_history": [getattr(n, "node_id", str(n)) for n in r.node_history],
                 "status": str(r.status)}
    dt = time.time() - t0
    text = str(r)
    return {"arch": arch, "task": task_name, "seconds": round(dt, 1),
            "billable_input": bill, "output_tokens": out,
            **grade(task_name, text), **extra, "answer_tail": text[-500:]}


if __name__ == "__main__":
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    rows = []
    for task_name, prompt in [("complex", COMPLEX), ("trivial", TRIVIAL)]:
        for arch in ("single", "subagent", "graph", "swarm"):
            for i in range(trials):
                print(f"[{task_name}/{arch}] trial {i+1}/{trials}", flush=True)
                try:
                    rows.append(run(arch, task_name, prompt) | {"trial": i + 1})
                except Exception as e:
                    rows.append({"arch": arch, "task": task_name, "trial": i + 1,
                                 "ERROR": f"{type(e).__name__}: {e}"[:300]})
    pathlib.Path(__file__).with_name("results_multiagent.json").write_text(json.dumps(rows, indent=2))

    for task_name in ("complex", "trivial"):
        print(f"\n{'='*78}\n{task_name.upper()}\n{'='*78}")
        print(f"{'arch':<10}{'billable_in':>13}{'out':>8}{'sec':>7}{'result':>28}")
        print("-" * 78)
        for arch in ("single", "subagent", "graph", "swarm"):
            v = [r for r in rows if r.get("arch") == arch and r.get("task") == task_name and "ERROR" not in r]
            if not v:
                err = next((r["ERROR"][:40] for r in rows if r.get("arch") == arch
                            and r.get("task") == task_name and "ERROR" in r), "?")
                print(f"{arch:<10}{'FAILED':>13}   {err}")
                continue
            if task_name == "trivial":
                res = f"{sum(r['correct'] for r in v)}/{len(v)} correct"
            else:
                res = (f"figs {statistics.mean(r['exact_figures'] for r in v):.1f}/6, "
                       f"worst {sum(r['named_worst'] for r in v)}/{len(v)}")
            print(f"{arch:<10}{statistics.median(r['billable_input'] for r in v):>13,.0f}"
                  f"{statistics.median(r['output_tokens'] for r in v):>8,.0f}"
                  f"{statistics.median(r['seconds'] for r in v):>7.1f}{res:>28}")
