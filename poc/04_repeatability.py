"""Does the crossover replicate, or was it one lucky pair of runs?

The article's headline number came from a single run per arm. A single run of a
non-deterministic system is an anecdote. This repeats each arm on each dataset and
reports the median and the spread, so the claim can be stated honestly.
"""
import json, statistics, sys, pathlib
import importlib

mod = importlib.import_module("02_context_economics") if False else None
sys.path.insert(0, str(pathlib.Path(__file__).parent))
econ = importlib.import_module("02_context_economics")

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUT = pathlib.Path(__file__).parent / "results_repeatability.json"


def main():
    rows = []
    for dataset in ("small", "large"):
        for arm, tools in econ.ARMS.items():
            for i in range(TRIALS):
                print(f"[{dataset}/{arm}] trial {i+1}/{TRIALS}", flush=True)
                try:
                    r = econ.run(arm, tools, dataset)
                    r["trial"] = i + 1
                except Exception as e:
                    r = {"dataset": dataset, "arm": arm, "trial": i + 1,
                         "ERROR": f"{type(e).__name__}: {e}"}
                rows.append(r)
    OUT.write_text(json.dumps(rows, indent=2))

    def stat(dataset, arm, key):
        vals = [r[key] for r in rows if r.get("dataset") == dataset
                and r.get("arm") == arm and key in r]
        return vals

    print(f"\n{'='*76}\nMEDIANS OVER {TRIALS} TRIALS\n{'='*76}")
    print(f"{'dataset':<8}{'arm':<22}{'billable_in':>13}{'range':>17}{'trips':>7}{'ok':>5}")
    print("-" * 76)
    summary = {}
    for dataset in ("small", "large"):
        for arm in econ.ARMS:
            b = stat(dataset, arm, "billable_input")
            t = stat(dataset, arm, "model_round_trips")
            ok = stat(dataset, arm, "all_figures_correct")
            if not b:
                print(f"{dataset:<8}{arm[:21]:<22}{'ALL FAILED':>13}")
                continue
            med = statistics.median(b)
            summary[(dataset, arm)] = med
            print(f"{dataset:<8}{arm[:21]:<22}{med:>13,.0f}"
                  f"{f'{min(b):,}-{max(b):,}':>17}{statistics.median(t):>7.0f}"
                  f"{f'{sum(ok)}/{len(ok)}':>5}")
    print()
    for dataset in ("small", "large"):
        a = summary.get((dataset, "A_one_call_at_a_time"))
        b = summary.get((dataset, "B_code_mode"))
        if a and b:
            print(f"{dataset:>6}: code mode is {(b-a)/a*100:+.0f}% vs one-call-at-a-time (median)")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
