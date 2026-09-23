"""G1: does tracing work the way `strands_harness/telemetry.py` says?

Source claim: the SDK already emits OpenTelemetry spans for the model loop, tool calls and
subagent delegation; the harness only wires an exporter, and only when the standard
`OTEL_TRACES_EXPORTER` variable is set. Unset means off.

Two runs in separate processes, since tracing setup is once per process:
  off   no variable set                      -> expect no spans
  on    OTEL_TRACES_EXPORTER=console         -> expect agent, model, tool and subagent spans

The console exporter prints spans to stdout, so the agent's own streaming is silenced with
`callback_handler=None`, leaving stdout to the exporter alone.
"""
import json, os, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).parent
CHILD = r'''
import sys, pathlib; sys.path.insert(0, "{here}")
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness
a = create_harness(model=MODEL, effort="off", memory=False, session=False, skills=False,
                   builtin_tools=["read", "subagent"], callback_handler=None)
assert_haiku(a)
a("Use the subagent tool to read {file} and report only its 'service' field.")
'''


def run(env_value):
    env = {k: v for k, v in os.environ.items() if k != "OTEL_TRACES_EXPORTER"}
    if env_value:
        env["OTEL_TRACES_EXPORTER"] = env_value
    first = sorted((HERE.parent / "data" / "incidents").glob("*.json"))[0]
    code = CHILD.format(here=HERE, file=first)
    p = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                       timeout=600)
    names = re.findall(r'^    "name": "([^"]+)"', p.stdout, re.M)
    return {"OTEL_TRACES_EXPORTER": env_value, "exit": p.returncode, "span_count": len(names),
            "span_names": sorted(set(names)), "stderr_tail": p.stderr[-300:]}


out = {"off": run(None), "on": run("console")}
pathlib.Path(__file__).with_name("results_tracing.json").write_text(json.dumps(out, indent=2))
for k, v in out.items():
    print(f"{k:<4} exit={v['exit']} spans={v['span_count']} names={v['span_names']}")
