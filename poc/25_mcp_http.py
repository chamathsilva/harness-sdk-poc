"""MCP over streamable HTTP, not stdio.

Experiment 16 connected a stdio MCP server. The config also accepts `url` for
streamable-http/sse, with `headers`, `transport` and OAuth `auth`. That path was
untested.

Start `mcp_http_server.py` first (it exposes `echo_upper` and `magic_number`), then run
this. The magic number is arbitrary and unguessable, so a correct answer proves the
tool was really called rather than invented.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL

load()
from strands_harness import create_harness

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8931
URL = f"http://127.0.0.1:{PORT}/mcp"
CONFIG = {"probe": {"url": URL}}                      # transport auto-detected from `url`
EXPLICIT = {"probe": {"url": URL, "transport": "streamable-http",
                      "headers": {"X-Probe": "harness-poc"}}}


def build(cfg):
    a = create_harness(model=MODEL, effort="off", builtin_tools=[], mcp_servers=cfg,
                       memory=False, session=False, skills=False,
                       builtin_plugins=[], context_manager=False)
    assert_haiku(a)
    return a


def main():
    out = {}

    for label, cfg in (("url only (transport auto-detected)", CONFIG),
                       ("explicit transport + headers", EXPLICIT)):
        print(f"\n=== {label} ===")
        try:
            agent = build(cfg)
            tools = sorted(agent.tool_names)
            mcp_tools = [t for t in tools if t.startswith("probe_")]
            print(f"tools: {tools}")
            answer = str(agent("Call your magic number tool and tell me the number it returns."))
            called = {k: v.call_count for k, v in agent.event_loop_metrics.tool_metrics.items()} \
                if hasattr(agent, "event_loop_metrics") else {}
            out[label] = {"tools": tools, "mcp_tools": mcp_tools,
                          "discovered": bool(mcp_tools),
                          "returned_4242": "4242" in answer,
                          "tool_calls": called, "answer": answer[-250:]}
            print(f"  mcp tools : {mcp_tools}")
            print(f"  got 4242  : {out[label]['returned_4242']}")
        except Exception as e:
            out[label] = {"ERROR": f"{type(e).__name__}: {e}"[:400]}
            print(f"  FAILED: {out[label]['ERROR']}")

    pathlib.Path(__file__).with_name("results_mcp_http.json").write_text(json.dumps(out, indent=2))
    print("\n" + "=" * 74)
    for label, r in out.items():
        if "ERROR" in r:
            print(f"{label:<38} ERROR: {r['ERROR'][:30]}")
        else:
            print(f"{label:<38} discovered={r['discovered']}  called_it={r['returned_4242']}")
    print("=" * 74)


main()
