"""Can you get typed data out, instead of prose you have to parse?

Anyone wiring an agent into a real service needs this: not a paragraph, but an object
that validates. Tests both routes the SDK offers, and whether structured output still
works when the agent had to use tools to find the answer.
"""
import json, pathlib, sys, importlib
from typing import Literal
from pydantic import BaseModel, Field
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
econ = importlib.import_module("02_context_economics")

D = econ.DATASETS["small"]
TRUTH = econ.ground_truth(D)
WORST = max(TRUTH, key=TRUTH.get)
FILES = sorted(f.name for f in D.glob("*.json"))


class ServiceTotal(BaseModel):
    service: str
    downtime_minutes: int


class IncidentReport(BaseModel):
    """A structured incident summary."""
    totals: list[ServiceTotal] = Field(description="Downtime per service, descending")
    worst_service: str = Field(description="The service with the most downtime")
    worst_minutes: int
    confidence: Literal["high", "medium", "low"]


TASK = (f"The directory {D} holds {len(FILES)} JSON incident records "
        f"({FILES[0]} to {FILES[-1]}), each with 'service' and 'downtime_minutes'. "
        "Total the downtime per service and identify the worst.")


def check(obj):
    got = {t.service: t.downtime_minutes for t in obj.totals}
    exact = sum(1 for k, v in TRUTH.items() if got.get(k) == v)
    return {"validated": True, "exact_figures": exact, "of": len(TRUTH),
            "worst_correct": obj.worst_service.lower() == WORST,
            "worst_minutes_correct": obj.worst_minutes == TRUTH[WORST],
            "confidence": obj.confidence, "parsed": got}


def main():
    out = {}

    print("=== route 1: agent.structured_output(Model, prompt) ===")
    a1 = create_harness(model=MODEL, effort="off",
                        builtin_tools=["read", "programmatic_tool_caller"],
                        memory=False, session=False, skills=False,
                        builtin_plugins=[], context_manager=False)
    assert_haiku(a1)
    try:
        obj = a1.structured_output(IncidentReport, TASK)
        out["structured_output"] = check(obj)
        print(f"  type: {type(obj).__name__}")
        print(json.dumps(out["structured_output"], indent=2))
    except Exception as e:
        out["structured_output"] = {"validated": False, "error": f"{type(e).__name__}: {e}"[:300]}
        print(f"  FAILED: {out['structured_output']['error']}")

    print("\n=== route 2: agent(prompt, structured_output_model=Model) ===")
    a2 = create_harness(model=MODEL, effort="off",
                        builtin_tools=["read", "programmatic_tool_caller"],
                        memory=False, session=False, skills=False,
                        builtin_plugins=[], context_manager=False)
    assert_haiku(a2)
    try:
        res = a2(TASK, structured_output_model=IncidentReport)
        obj2 = res.structured_output
        out["via_call"] = check(obj2) | {"result_type": type(res).__name__}
        print(f"  structured_output attr: {type(obj2).__name__}")
        print(json.dumps({k: v for k, v in out["via_call"].items() if k != "parsed"}, indent=2))
    except Exception as e:
        out["via_call"] = {"validated": False, "error": f"{type(e).__name__}: {e}"[:300]}
        print(f"  FAILED: {out['via_call']['error']}")

    pathlib.Path(__file__).with_name("results_structured_output.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 70)
    for k, v in out.items():
        if v.get("validated"):
            print(f"{k:<20} validated, {v['exact_figures']}/{v['of']} figures exact, "
                  f"worst correct: {v['worst_correct']}")
        else:
            print(f"{k:<20} FAILED: {v.get('error','')[:50]}")
    print("=" * 70)


main()
