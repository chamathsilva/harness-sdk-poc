"""What does a default create_harness() send the model on turn one? Twin of 30.

Makes NO model calls: reads the system prompt and tool specs off the built agent.
Counted the same way as 30 (json.dumps of the tool list) so the two are comparable.

Run with the current env:  cd poc && ../.venv-new/bin/python 31_strands_surface.py
Writes results_strands_surface.json.
"""
import json, os, pathlib
from _env import MODEL

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-dummy-no-calls")

import strands_harness
from strands_harness import create_harness

agent = create_harness(model=MODEL, effort="off")
specs = agent.tool_registry.get_all_tool_specs()
out = {
    "strands_harness": getattr(strands_harness, "__version__", "?"),
    "tools": sorted(s["name"] for s in specs),
    "tool_count": len(specs),
    "tool_schema_chars": len(json.dumps(specs)),
    "system_prompt_chars": len(agent.system_prompt or ""),
    "environment": type(getattr(agent, "environment", None)).__name__,
}
for k, v in out.items():
    print(f"{k}: {v}")
pathlib.Path(__file__).with_name("results_strands_surface.json").write_text(json.dumps(out, indent=2))
print("wrote results_strands_surface.json")
