"""N4: is code mode really dearer on small data?

The original claim ("~3x worse on 16 KB") rested on n=7 for code mode, and the two arms'
ranges overlapped. This re-runs BOTH arms fresh on the current release, n=12 each, with the
trials interleaved (A, B, A, B, ...) so any drift over the run affects both arms equally.

Same task, same grader and same billable metric as `02` / `04`. Results are written to a
file after every trial, because the agent's streaming output makes stdout unparseable.
"""
import importlib, json, pathlib, re, statistics, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load

load()
import strands_harness

econ = importlib.import_module("02_context_economics")
SERVICES = "notifications|auth|inventory|checkout|search|payments"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
OUT = pathlib.Path(__file__).with_name("results_small_crossover.json")
TRUTH = econ.ground_truth(econ.DATASETS["small"])


def exact(text):
    found = dict(re.findall(rf"({SERVICES})\W{{0,4}}(\d[\d,]*)", text, re.I))
    found = {k.lower(): int(v.replace(",", "")) for k, v in found.items()}
    return sum(1 for k in TRUTH if found.get(k) == TRUTH[k])


rows = []
for i in range(N):
    for arm, tools in econ.ARMS.items():
        print(f"[{arm}] trial {i + 1}/{N}", flush=True)
        try:
            r = econ.run(arm, tools, "small")
            r["exact"] = exact(r["answer_tail"])
        except Exception as e:
            r = {"arm": arm, "ERROR": f"{type(e).__name__}: {e}"[:300]}
        r.update(trial=i + 1, harness_version=strands_harness.__version__
                 if hasattr(strands_harness, "__version__") else None)
        rows.append(r)
        OUT.write_text(json.dumps(rows, indent=2))

ok = [r for r in rows if "ERROR" not in r]
print("\n" + "=" * 72)
for arm in econ.ARMS:
    v = [r["billable_input"] for r in ok if r["arm"] == arm]
    e = [r["exact"] for r in ok if r["arm"] == arm]
    if v:
        print(f"{arm:<40} n={len(v):<3} median={statistics.median(v):>8,.0f}  "
              f"range={min(v):,}-{max(v):,}  perfect={sum(x == 6 for x in e)}/{len(e)}")
print("=" * 72)
