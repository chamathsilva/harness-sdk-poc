"""A/B: does code-mode tool orchestration actually change agent economics?

Same model, same task, same data. The only variable is whether the agent may write
code that drives its own tools (`programmatic_tool_caller`), or must call them one
at a time (`read` only).

Two datasets, because the answer turns out to depend on payload shape:
  small -- 40 tiny records (~16 KB total)
  large -- the same 40 records, each carrying a 60-line log tail (~210 KB total)

Runs on Anthropic's API with a cheap model on purpose: the claim under test is
*relative* (round trips, token growth), a property of the orchestration pattern
rather than the model tier.

Usage:  python 02_context_economics.py [small|large] [arm-substring]
"""
import sys, time, json, pathlib
from _env import load, assert_haiku, MODEL
load()

from strands_harness import create_harness

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATASETS = {"small": ROOT / "data" / "incidents",
            "large": ROOT / "data" / "incidents_large"}

EFFORT = "off"
# Memory/sessions/skills off so the measurement isn't polluted by background
# extraction calls or state carried between arms. Tool set is the only variable.
COMMON = dict(model=MODEL, effort=EFFORT, memory=False, session=False,
              skills=False, builtin_plugins=[], context_manager=False)

ARMS = {"A_one_call_at_a_time": ["read"],
        "B_code_mode":          ["read", "programmatic_tool_caller"]}


def ground_truth(d):
    tot = {}
    for f in sorted(d.glob("*.json")):
        r = json.loads(f.read_text())
        tot[r["service"]] = tot.get(r["service"], 0) + r["downtime_minutes"]
    return dict(sorted(tot.items(), key=lambda kv: -kv[1]))


def build_task(d):
    files = sorted(f.name for f in d.glob("*.json"))
    # The file list is handed to both arms. Discovery is not what's measured:
    # `read` takes absolute paths and cannot list a directory, so making the agent
    # hunt for files would measure flailing, not orchestration.
    return (f"The directory {d} contains {len(files)} JSON incident records, named "
            f"{files[0]} through {files[-1]} (every INC-#### in that range). Each record "
            "has a 'service' field and a 'downtime_minutes' field. Read all of them, then "
            "report the total downtime minutes per service sorted descending, and name the "
            "single worst service. Use absolute paths. Report exact numbers.")


def run(name, builtin_tools, dataset):
    d = DATASETS[dataset]
    truth = ground_truth(d)
    agent = create_harness(builtin_tools=builtin_tools, **COMMON)
    assert_haiku(agent)
    t0 = time.time()
    result = agent(build_task(d))
    dt = time.time() - t0
    m, u = result.metrics, result.metrics.accumulated_usage
    calls = {k: v.call_count for k, v in m.tool_metrics.items()}
    text = str(result)
    return {
        "dataset": dataset, "arm": name, "tools": builtin_tools,
        "model": MODEL, "effort": EFFORT,
        "model_round_trips": m.cycle_count,
        "usage_full": dict(u),
        "input_tokens": u["inputTokens"], "output_tokens": u["outputTokens"],
        "total_tokens": u["totalTokens"],
        # Cache writes are billed; without them the comparison flatters whichever
        # arm happened to cache more.
        "billable_input": u["inputTokens"] + u.get("cacheReadInputTokens", 0)
                          + u.get("cacheWriteInputTokens", 0),
        "tool_calls": calls, "total_tool_calls": sum(calls.values()),
        "seconds": round(dt, 1),
        "all_figures_correct": all(str(v) in text for v in truth.values()),
        "answer_tail": text[-400:],
    }


if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else "small"
    only = sys.argv[2] if len(sys.argv) > 2 else None
    assert dataset in DATASETS, f"dataset must be one of {list(DATASETS)}"
    out = []
    for name, tools in ARMS.items():
        if only and only not in name:
            continue
        print(f"\n{'='*70}\n{dataset.upper()} / {name}  tools={tools}\n{'='*70}", flush=True)
        try:
            r = run(name, tools, dataset)
        except Exception as e:
            r = {"dataset": dataset, "arm": name, "ERROR": f"{type(e).__name__}: {e}"}
        print(json.dumps({k: v for k, v in r.items() if k != "answer_tail"}, indent=2), flush=True)
        out.append(r)
    p = pathlib.Path(__file__).parent / f"results_{dataset}.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {p}")
