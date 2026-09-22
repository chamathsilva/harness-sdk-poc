"""Control: is the accuracy gap caused by code mode, or by my own effort="off" setting?

The repeatability run disabled reasoning to keep costs down. That is exactly the
setting that would hurt an agent doing arithmetic in its head while leaving the
program-writing arm untouched -- a confound of my own making. This re-runs the
weaker arm with reasoning ON to see whether the gap survives.
"""
import json, re, sys, pathlib, statistics
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
import importlib
econ = importlib.import_module("02_context_economics")

TRUTH = econ.ground_truth
SERVICES = "notifications|auth|inventory|checkout|search|payments"
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 3


def grade(dataset, text):
    truth = TRUTH(econ.DATASETS[dataset])
    found = dict(re.findall(rf"({SERVICES})\W{{0,4}}(\d[\d,]*)", text, re.I))
    found = {k.lower(): int(v.replace(",", "")) for k, v in found.items()}
    return sum(1 for k in truth if found.get(k) == truth[k]), len(truth)


def run_once(dataset, tools, effort):
    agent = create_harness(model=MODEL, effort=effort, builtin_tools=tools,
                           memory=False, session=False, skills=False,
                           builtin_plugins=[], context_manager=False)
    assert_haiku(agent)
    result = agent(econ.build_task(econ.DATASETS[dataset]))
    u = result.metrics.accumulated_usage
    ok, n = grade(dataset, str(result))
    return {"exact": ok, "of": n,
            "billable_input": u["inputTokens"] + u.get("cacheReadInputTokens", 0)
                              + u.get("cacheWriteInputTokens", 0),
            "output_tokens": u["outputTokens"],
            "round_trips": result.metrics.cycle_count}


if __name__ == "__main__":
    out = []
    for dataset in ("small", "large"):
        for effort in ("off", "high"):
            for i in range(TRIALS):
                print(f"[{dataset}] arm A, effort={effort}, trial {i+1}", flush=True)
                try:
                    r = run_once(dataset, ["read"], effort)
                except Exception as e:
                    r = {"ERROR": f"{type(e).__name__}: {e}"}
                r |= {"dataset": dataset, "effort": effort, "trial": i + 1}
                out.append(r)
    pathlib.Path(__file__).with_name("results_control_effort.json").write_text(json.dumps(out, indent=2))

    print(f"\n{'='*70}\nARM A (one call at a time) -- does reasoning fix the arithmetic?\n{'='*70}")
    print(f"{'dataset':<9}{'effort':<8}{'exact figures':>16}{'median billable_in':>21}")
    print("-" * 70)
    for dataset in ("small", "large"):
        for effort in ("off", "high"):
            v = [r for r in out if r.get("dataset") == dataset and r.get("effort") == effort and "exact" in r]
            if not v:
                print(f"{dataset:<9}{effort:<8}{'ALL FAILED':>16}")
                continue
            print(f"{dataset:<9}{effort:<8}"
                  f"{f'{statistics.mean(r[chr(101)+chr(120)+chr(97)+chr(99)+chr(116)] for r in v):.1f}/6':>16}"
                  f"{statistics.median(r['billable_input'] for r in v):>21,.0f}")
