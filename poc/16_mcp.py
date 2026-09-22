"""Does mcp_servers= actually work, and what does it give the agent?

The article series claims you point the harness at a standard mcpServers config and it
connects, discovers tools, and namespaces them. Untested until now. Also tests the
resilience claim: a server that fails to start should contribute no tools rather than
taking the agent down.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness

ROOT = pathlib.Path(__file__).resolve().parent.parent
INCIDENTS = ROOT / "data" / "incidents"

GOOD = {"incidents": {"command": "npx",
                      "args": ["-y", "@modelcontextprotocol/server-filesystem", str(INCIDENTS)]}}
# A server that cannot possibly start, to test failure isolation.
BROKEN = {"broken": {"command": "definitely-not-a-real-command", "args": []},
          "incidents": GOOD["incidents"]}


def build(mcp, **kw):
    a = create_harness(model=MODEL, effort="off", builtin_tools=[], mcp_servers=mcp,
                       memory=False, session=False, skills=False,
                       builtin_plugins=[], context_manager=False, **kw)
    assert_haiku(a)
    return a


def main():
    out = {}

    print("=== 1. connecting to a filesystem MCP server ===")
    agent = build(GOOD)
    tools = sorted(agent.tool_names)
    mcp_tools = [t for t in tools if t.startswith("incidents_")]
    print(f"all tools     : {tools}")
    print(f"mcp tools     : {mcp_tools}")
    print(f"namespaced    : {bool(mcp_tools)}")

    # Can the model actually use one?
    r = agent(f"Using only your MCP tools, list the files in {INCIDENTS} and tell me how many there are.")
    text = str(r)
    used = {k: v.call_count for k, v in r.metrics.tool_metrics.items()}
    counted = "40" in text
    print(f"tool calls    : {used}")
    print(f"found 40 files: {counted}")
    out["connected"] = {"all_tools": tools, "mcp_tools": mcp_tools,
                        "tool_calls": used, "counted_40": counted, "answer": text[-400:]}

    print("\n=== 2. a broken server alongside a good one ===")
    try:
        agent2 = build(BROKEN)
        tools2 = sorted(agent2.tool_names)
        still_has = [t for t in tools2 if t.startswith("incidents_")]
        print(f"agent built   : True")
        print(f"tools present : {tools2}")
        print(f"good server survived: {bool(still_has)}")
        out["broken_server"] = {"agent_built": True, "tools": tools2,
                                "good_server_survived": bool(still_has)}
    except Exception as e:
        print(f"agent build FAILED: {type(e).__name__}: {e}"[:300])
        out["broken_server"] = {"agent_built": False, "error": f"{type(e).__name__}: {e}"[:300]}

    pathlib.Path(__file__).with_name("results_mcp.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 70)
    print(f"MCP tools discovered and namespaced : {bool(mcp_tools)}")
    print(f"model used them successfully        : {counted}")
    print(f"broken server isolated              : {out['broken_server'].get('good_server_survived', False)}")
    print("=" * 70)


main()
