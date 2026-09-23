"""N2 live capture: what do the usage fields report on a cached Anthropic run?

Upstream issue #3546 says that on the Anthropic API `totalTokens` is recomputed as
input + output and so leaves cached tokens out, while Anthropic documents the true input
as input + cache_read + cache_creation. This captures the fields directly on the current
release: two calls on one agent, so the second can read the cache the first wrote.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL

load()
from strands_harness import create_harness

a = create_harness(model=MODEL, effort="off", memory=False, session=False, skills=False,
                   callback_handler=None)          # default toolset: large enough to cache
assert_haiku(a)

rows = []
for i, prompt in enumerate(["Reply with the single word: ready.",
                            "Reply with the single word: again."], 1):
    u = dict(a(prompt).metrics.accumulated_usage)   # cumulative across the agent's calls
    inp, out = u["inputTokens"], u["outputTokens"]
    cr, cw = u.get("cacheReadInputTokens", 0), u.get("cacheWriteInputTokens", 0)
    rows.append({"call": i, "usage": u,
                 "totalTokens": u["totalTokens"],
                 "input_plus_output": inp + out,
                 "true_input_per_anthropic_docs": inp + cr + cw,
                 "totalTokens_includes_cache": u["totalTokens"] == inp + out + cr + cw,
                 "share_of_input_missing_from_totalTokens":
                     round((cr + cw) / (inp + cr + cw), 3) if (inp + cr + cw) else 0})

out = pathlib.Path(__file__).with_name("results_usage_fields.json")
out.write_text(json.dumps(rows, indent=2))
for r in rows:
    print(json.dumps(r))
