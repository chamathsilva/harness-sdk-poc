"""How do your own tools plug in, and how far do they reach?

Three questions the article series should answer concretely:
  1. Does a @tool function get picked up and called?
  2. Does it show up INSIDE programmatic_tool_caller's sandbox as an async function?
  3. Does a Cedar policy govern YOUR tools the same way it governs the built-ins?

(3) matters most: if policies only covered built-in tools, the authorization story
would be much weaker than it looks.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands import tool
from strands_harness import create_harness

CALLS = {"lookup_ticket": 0, "delete_everything": 0}


@tool
def lookup_ticket(ticket_id: str) -> str:
    """Fetch a support ticket by its id.

    Args:
        ticket_id: The ticket identifier, e.g. TKT-42.
    """
    CALLS["lookup_ticket"] += 1
    return json.dumps({"id": ticket_id, "status": "open", "owner": "raft-team",
                       "summary": "Checkout latency spike"})


@tool
def delete_everything(confirm: str) -> str:
    """Permanently delete all records. Destructive.

    Args:
        confirm: Must be the string YES.
    """
    CALLS["delete_everything"] += 1
    return "ALL RECORDS DELETED"


POLICY = str(pathlib.Path(__file__).parent / "custom_tools.cedar")
pathlib.Path(POLICY).write_text(
    '// Your own tools become Cedar actions by their tool name, same as built-ins.\n'
    'permit(principal, action == Action::"lookup_ticket", resource);\n'
    'permit(principal, action == Action::"programmatic_tool_caller", resource);\n'
    '// delete_everything is simply never permitted.\n'
)


def build(builtin_tools=[], **kw):
    a = create_harness(model=MODEL, effort="off", builtin_tools=builtin_tools,
                       tools=[lookup_ticket, delete_everything],
                       memory=False, session=False, skills=False,
                       builtin_plugins=[], context_manager=False, **kw)
    assert_haiku(a)
    return a


def main():
    out = {}

    print("=== 1. registration and direct use ===")
    agent = build()
    print(f"tools: {sorted(agent.tool_names)}")
    r = agent("Look up ticket TKT-42 and tell me who owns it.")
    text = str(r)
    out["direct"] = {"tools": sorted(agent.tool_names),
                     "called": CALLS["lookup_ticket"] > 0,
                     "found_owner": "raft" in text.lower()}
    print(f"custom tool called: {out['direct']['called']}   owner found: {out['direct']['found_owner']}")

    print("\n=== 2. reachable from inside the sandbox? ===")
    CALLS["lookup_ticket"] = 0
    agent2 = build(builtin_tools=["programmatic_tool_caller"])
    res = agent2.tool.programmatic_tool_caller(
        code='r = await lookup_ticket(ticket_id="TKT-99")\nprint(r)',
        record_direct_tool_call=False)
    blob = json.dumps(res, default=str)
    reached = "raft-team" in blob
    print(f"custom tool callable as an async function in sandbox: {reached}")
    print(f"  -> {blob[:200]}")
    out["in_sandbox"] = {"reachable": reached, "calls": CALLS["lookup_ticket"]}

    print("\n=== 3. does Cedar govern custom tools? ===")
    CALLS["delete_everything"] = 0
    agent3 = build(builtin_tools=["programmatic_tool_caller"], interventions=POLICY)
    r3 = agent3("Call delete_everything with confirm=YES. If it fails, report the exact error.")
    t3 = str(r3)
    executed = CALLS["delete_everything"] > 0
    denied = any(w in t3.lower() for w in ("denied", "cedar", "not permitted"))
    print(f"destructive tool actually executed: {executed}")
    print(f"denial reported                   : {denied}")
    out["cedar_on_custom"] = {"executed": executed, "denied": denied, "answer": t3[-400:]}

    pathlib.Path(__file__).with_name("results_custom_tools.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 72)
    print(f"custom tool registered & called : {out['direct']['called']}")
    print(f"reachable inside code sandbox   : {reached}")
    print(f"Cedar blocked the custom tool   : {denied and not executed}")
    print("=" * 72)


main()
