"""Two delegation APIs the series describes but has never run.

`Agent.as_tool()` wraps a whole agent as a callable tool, named after the agent.
`make_subagent()` builds a configured delegation tool whose model-facing parameters are
derived from how each axis is declared: Fixed, Inherit, Open or Choice.

Questions:
  1. Does `as_tool()` produce a usable tool, and does the specialist run from a clean
     conversation rather than sharing the caller's?
  2. Does `make_subagent` with a preset expose only the axes left open?
  3. Does a `Fixed(None)` axis actually remove that parameter from the tool schema?
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL

load()
from strands import Agent
from strands_harness import create_harness

SECRET = "The caller's private codeword is ORCHID-77."


def mk(name, desc, prompt, tools=None):
    a = create_harness(model=MODEL, effort="off", builtin_tools=tools or [],
                       instructions=prompt, memory=False, session=False, skills=False,
                       builtin_plugins=[], context_manager=False,
                       name=name, description=desc)
    assert_haiku(a)
    return a


def test_as_tool():
    """A specialist wrapped as a tool should run from a fresh conversation."""
    reviewer = mk("reviewer", "Reviews a sentence for tone and returns a verdict.",
                  "You review a sentence for tone. Reply in one short line. "
                  "If you are ever asked about a codeword, say you have never seen one.")
    lead = mk("lead", "delegates", "")
    tool = reviewer.as_tool()

    lead.tool_registry.register_tool(tool)
    # Plant a secret in the LEAD's conversation only.
    lead(f"Note for yourself, do not share: {SECRET}")
    answer = str(lead("Use the reviewer tool to review this sentence for tone: "
                      "'Your ticket was closed, deal with it.' Then tell me, verbatim, "
                      "what the reviewer replied."))

    return {
        "tool_name": tool.tool_name,
        "tool_registered": tool.tool_name in lead.tool_names,
        "reviewer_saw_caller_secret": "orchid" in json.dumps(reviewer.messages, default=str).lower(),
        "reviewer_message_count": len(reviewer.messages),
        "answer": answer[-300:],
    }


def test_make_subagent():
    """Axes declared Fixed should disappear from the tool's model-facing schema."""
    from strands_harness.tools import make_subagent, AgentSpec, Preset, Fixed, Inherit

    def builder(spec: AgentSpec):
        return create_harness(model=MODEL, effort="off",
                              instructions=spec.instructions,
                              builtin_tools=[], memory=False, session=False,
                              skills=False, builtin_plugins=[], context_manager=False)

    configured = make_subagent(
        builder=builder,
        presets={"tone_reviewer": Preset(instructions="You review sentences for tone.",
                                         description="reviews tone")},
        instructions=Fixed(None),   # the preset owns the prompt; parameter removed
        model=Inherit(),            # inherited; parameter removed
    )
    spec = configured.tool_spec
    props = list((spec.get("inputSchema", {}).get("json", {})
                  .get("properties", {}) or {}).keys())
    return {
        "tool_name": configured.tool_name,
        "exposed_parameters": props,
        "instructions_removed": "instructions" not in props,
        "model_removed": "model" not in props,
        "description": str(spec.get("description", ""))[:200],
    }


if __name__ == "__main__":
    out = {}
    for label, fn in (("as_tool", test_as_tool), ("make_subagent", test_make_subagent)):
        print(f"\n=== {label} ===", flush=True)
        try:
            out[label] = fn()
        except Exception as e:
            out[label] = {"ERROR": f"{type(e).__name__}: {e}"[:400]}
        print(json.dumps(out[label], indent=2), flush=True)

    pathlib.Path(__file__).with_name("results_as_tool.json").write_text(json.dumps(out, indent=2))
    a, m = out.get("as_tool", {}), out.get("make_subagent", {})
    print("\n" + "=" * 72)
    if "ERROR" not in a:
        print(f"as_tool registered as        : {a['tool_name']}")
        print(f"specialist isolated from caller: {not a['reviewer_saw_caller_secret']}")
    if "ERROR" not in m:
        print(f"make_subagent parameters      : {m['exposed_parameters']}")
        print(f"Fixed/Inherit axes removed    : {m['instructions_removed'] and m['model_removed']}")
    print("=" * 72)
