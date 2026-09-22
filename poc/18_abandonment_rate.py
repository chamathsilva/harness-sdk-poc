"""How often does the model abandon the sandbox? Article 1 says "roughly a quarter".

That claim rests on 12 runs, only 9 of them instrumented. This runs a larger
instrumented batch on the bulky dataset, recording tool calls every time, so the
fallback rate can be stated with a real denominator.

A run is classed as "fell back" when it made 10 or more direct `read` calls -- i.e.
it went and fetched the files itself instead of letting sandboxed code do it.
"""
import json, pathlib, re, statistics, sys, importlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
econ = importlib.import_module("02_context_economics")

SERVICES = "notifications|auth|inventory|checkout|search|payments"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 15


def grade(text):
    truth = econ.ground_truth(econ.DATASETS["large"])
    f = dict(re.findall(rf"({SERVICES})\W{{0,4}}(\d[\d,]*)", text, re.I))
    f = {k.lower(): int(v.replace(",", "")) for k, v in f.items()}
    return sum(1 for k in truth if f.get(k) == truth[k])


rows = []
for i in range(N):
    print(f"trial {i+1}/{N}", flush=True)
    try:
        a = create_harness(model=MODEL, effort="off",
                           builtin_tools=["read", "programmatic_tool_caller"],
                           memory=False, session=False, skills=False,
                           builtin_plugins=[], context_manager=False)
        assert_haiku(a)
        r = a(econ.build_task(econ.DATASETS["large"]))
        u = r.metrics.accumulated_usage
        calls = {k: v.call_count for k, v in r.metrics.tool_metrics.items()}
        rows.append({"trial": i + 1, "direct_reads": calls.get("read", 0),
                     "sandbox_calls": calls.get("programmatic_tool_caller", 0),
                     "billable_input": u["inputTokens"] + u.get("cacheReadInputTokens", 0)
                                       + u.get("cacheWriteInputTokens", 0),
                     "round_trips": r.metrics.cycle_count, "exact": grade(str(r))})
    except Exception as e:
        rows.append({"trial": i + 1, "ERROR": f"{type(e).__name__}: {e}"[:200]})

pathlib.Path(__file__).with_name("results_abandonment.json").write_text(json.dumps(rows, indent=2))
ok = [r for r in rows if "ERROR" not in r]
fell = [r for r in ok if r["direct_reads"] >= 10]
used = [r for r in ok if r["direct_reads"] < 10]
print(f"\n{'='*70}\nSANDBOX ABANDONMENT RATE (bulky dataset, n={len(ok)})\n{'='*70}")
print(f"used the sandbox : {len(used):>3}/{len(ok)}  median {statistics.median(r['billable_input'] for r in used):>9,.0f}  "
      f"perfect {sum(1 for r in used if r['exact']==6)}/{len(used)}" if used else "none used sandbox")
if fell:
    print(f"fell back to read: {len(fell):>3}/{len(ok)}  median {statistics.median(r['billable_input'] for r in fell):>9,.0f}  "
          f"perfect {sum(1 for r in fell if r['exact']==6)}/{len(fell)}")
else:
    print("fell back to read:   0 — no fallback observed in this batch")
print(f"\nfallback rate: {len(fell)}/{len(ok)} = {len(fell)/max(len(ok),1)*100:.0f}%")
print(f"runs over 100k billable: {sum(1 for r in ok if r['billable_input']>100_000)}/{len(ok)}")
