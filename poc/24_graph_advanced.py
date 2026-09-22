"""Two Graph features the series mentions but has never exercised.

1. Conditional edges -- `add_edge(..., condition=...)`. A classifier decides which
   branch runs. The test is that the OTHER branch genuinely does not execute, not
   merely that the answer looks right.
2. Nested graphs -- a Graph used as a node inside another Graph.

Both are run twice with opposite inputs, so a graph that always takes one path cannot
pass by luck.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL, HAIKU

load()
from strands_harness import create_harness
from strands.multiagent import GraphBuilder


def mk(name, desc, prompt):
    """A plain `strands.Agent`, NOT a harness agent.

    This matters and cost a run to learn. A harness agent carries HARNESS_CONTRACT,
    which tells it to keep working until the task is resolved. Asked to classify an
    outage in one word, it starts troubleshooting instead: 149 words beginning "There
    are no background recovery tasks currently running...". A plain Agent with the same
    prompt replies "URGENT". See `results_node_agent_choice.json`.

    Narrow, deterministic pipeline steps want a plain Agent. Use a harness agent for a
    node only where you actually want autonomy.
    """
    from strands import Agent
    from strands.models.anthropic import AnthropicModel
    return Agent(model=AnthropicModel(model_id=HAIKU, max_tokens=256),
                 system_prompt=prompt, name=name, description=desc)


def said(state, node_id, needle):
    return needle.lower() in str((state.results or {}).get(node_id, "")).lower()


def build_conditional():
    b = GraphBuilder()
    b.add_node(mk("classifier", "classifies an incident",
                  "Classify the incident. Reply with exactly one word: URGENT or ROUTINE. "
                  "A total outage or data loss is URGENT. Anything cosmetic is ROUTINE."), "classifier")
    b.add_node(mk("pager", "pages the on-call engineer",
                  "Write one line: who to page and why. Begin with 'PAGED:'."), "pager")
    b.add_node(mk("ticket", "files a low-priority ticket",
                  "Write one line describing the ticket filed. Begin with 'TICKETED:'."), "ticket")
    b.add_edge("classifier", "pager", condition=lambda s: said(s, "classifier", "urgent"))
    b.add_edge("classifier", "ticket", condition=lambda s: not said(s, "classifier", "urgent"))
    b.set_entry_point("classifier")
    b.set_max_node_executions(6)
    return b.build()


def build_nested():
    """An inner two-stage graph, used as a single node inside an outer graph."""
    ib = GraphBuilder()
    ib.add_node(mk("doubler", "doubles a number", "Output only the given number doubled."), "doubler")
    ib.add_node(mk("adder", "adds ten", "Output only the given number plus 10."), "adder")
    ib.add_edge("doubler", "adder")
    ib.set_entry_point("doubler")
    ib.set_max_node_executions(4)
    inner = ib.build()

    ob = GraphBuilder()
    ob.add_node(inner, "inner_maths")          # a Graph as a node
    ob.add_node(mk("reporter", "reports the final figure",
                   "State the final number you were given, as 'RESULT: <number>'."), "reporter")
    ob.add_edge("inner_maths", "reporter")
    ob.set_entry_point("inner_maths")
    ob.set_max_node_executions(6)
    return ob.build()


if __name__ == "__main__":
    out = {"conditional": [], "nested": None}

    print("=== conditional edges ===")
    for label, prompt in [("urgent input", "The payments database is down and customers cannot check out."),
                          ("routine input", "A button on the settings page is two pixels off centre.")]:
        try:
            r = build_conditional()(prompt)
            order = [getattr(n, "node_id", str(n)) for n in r.execution_order]
            rec = {"input": label, "execution_order": order,
                   "pager_ran": "pager" in order, "ticket_ran": "ticket" in order,
                   "took_exactly_one_branch": ("pager" in order) != ("ticket" in order),
                   "answer": str(r)[-200:]}
        except Exception as e:
            rec = {"input": label, "ERROR": f"{type(e).__name__}: {e}"[:300]}
        print(json.dumps({k: v for k, v in rec.items() if k != "answer"}, indent=2), flush=True)
        out["conditional"].append(rec)

    print("\n=== nested graph (5 -> double -> +10 -> report) ===")
    try:
        r = build_nested()("5")
        order = [getattr(n, "node_id", str(n)) for n in r.execution_order]
        out["nested"] = {"execution_order": order, "status": str(r.status),
                         "reached_15": "15" in str(r), "answer": str(r)[-200:]}
    except Exception as e:
        out["nested"] = {"ERROR": f"{type(e).__name__}: {e}"[:300]}
    print(json.dumps(out["nested"], indent=2))

    pathlib.Path(__file__).with_name("results_graph_advanced.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 72)
    c = [r for r in out["conditional"] if "ERROR" not in r]
    if len(c) == 2:
        routed = c[0]["pager_ran"] and not c[0]["ticket_ran"] and c[1]["ticket_ran"] and not c[1]["pager_ran"]
        print(f"conditional routing correct both ways : {routed}")
        print(f"  urgent  -> {c[0]['execution_order']}")
        print(f"  routine -> {c[1]['execution_order']}")
    n = out["nested"]
    if "ERROR" not in n:
        print(f"nested graph executed                 : {n['execution_order']}, reached 15: {n['reached_15']}")
    print("=" * 72)
