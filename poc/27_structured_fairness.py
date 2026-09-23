"""N5 fairness control: is the deprecated `agent.structured_output()` broken, or misused?

Its docstring says it answers from "the existing conversation history" and, per the
source, it makes one model call with no tools. Our earlier 3/3 fabrication came from
calling it on a FRESH agent and asking it to analyse files it could not read. That shows
what the method does, not that it is broken. The fair test adds the case it was designed
for:

  cold       fresh agent, structured_output(Model, TASK)  -- the original experiment
  warm       agent(TASK) first, then structured_output(Model) on that conversation
  supported  agent(TASK, structured_output_model=Model)   -- the documented replacement

Also recorded: whether a DeprecationWarning fired, and whether any tool call happened
during the structured_output() call itself.
"""
import importlib, json, pathlib, sys, warnings

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL

load()
from strands_harness import create_harness

import types
from typing import Literal
from pydantic import BaseModel, Field

# Same schema, task and grader as `20_structured_output.py`, copied rather than imported:
# that script runs its experiment at import time.
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


so = types.SimpleNamespace(IncidentReport=IncidentReport, TASK=TASK, check=check)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUT = pathlib.Path(__file__).with_name("results_structured_fairness.json")


def build():
    a = create_harness(model=MODEL, effort="off",
                       builtin_tools=["read", "programmatic_tool_caller"],
                       memory=False, session=False, skills=False,
                       builtin_plugins=[], context_manager=False)
    assert_haiku(a)
    return a


def tool_calls(agent):
    m = getattr(agent, "event_loop_metrics", None)
    return sum(t.call_count for t in m.tool_metrics.values()) if m else None


def call_legacy(agent, *args):
    """Run the deprecated method, capturing warnings and any tool calls it makes."""
    before = tool_calls(agent)
    msgs_before = len(agent.messages)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        obj = agent.structured_output(so.IncidentReport, *args)
    return obj, {
        "deprecation_warning": any(issubclass(x.category, DeprecationWarning) for x in w),
        "tool_calls_during_call": (tool_calls(agent) or 0) - (before or 0),
        "messages_added": len(agent.messages) - msgs_before,
    }


rows = []
for i in range(N):
    for arm in ("cold", "warm", "supported"):
        print(f"[{arm}] trial {i + 1}/{N}", flush=True)
        rec = {"arm": arm, "trial": i + 1}
        try:
            a = build()
            if arm == "cold":
                obj, meta = call_legacy(a, so.TASK)
            elif arm == "warm":
                a(so.TASK)                        # the agent does the work with its tools
                rec["tool_calls_before"] = tool_calls(a)
                obj, meta = call_legacy(a)        # then structure what it found
            else:
                obj, meta = a(so.TASK, structured_output_model=so.IncidentReport).structured_output, {}
                rec["tool_calls_before"] = tool_calls(a)
            rec |= meta | {k: v for k, v in so.check(obj).items() if k != "parsed"}
        except Exception as e:
            rec["ERROR"] = f"{type(e).__name__}: {e}"[:300]
        rows.append(rec)
        OUT.write_text(json.dumps(rows, indent=2))

print("\n" + "=" * 76)
for arm in ("cold", "warm", "supported"):
    r = [x for x in rows if x["arm"] == arm and "ERROR" not in x]
    if r:
        print(f"{arm:<10} perfect={sum(x['exact_figures'] == 6 for x in r)}/{len(r)}  "
              f"figures={[x['exact_figures'] for x in r]}  "
              f"deprecation_warning={all(x.get('deprecation_warning', False) for x in r) if arm != 'supported' else 'n/a'}  "
              f"tools_during_call={[x.get('tool_calls_during_call') for x in r] if arm != 'supported' else 'n/a'}")
print("=" * 76)
