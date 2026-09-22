"""What does one create_harness() call actually assemble?"""
import json
from _env import load, assert_haiku, MODEL
load()

from strands_harness import create_harness, HARNESS_CONTRACT

agent = create_harness(model=MODEL, effort="off")

print("=== TYPE ===");  print(type(agent).__module__ + "." + type(agent).__name__)
print("\n=== MODEL ===")
m = agent.model
print(type(m).__name__, json.dumps(m.get_config(), default=str)[:400])
print("\n=== TOOLS ===")
print(sorted(agent.tool_names))
print("\n=== PLUGINS ===")
print([type(p).__name__ for p in getattr(agent, "plugins", [])])
print("\n=== SESSION ===", getattr(agent, "session_id", None))
print("=== CONTEXT MGR ===", type(getattr(agent, "context_manager", None)).__name__)
print("=== MEMORY ===", type(getattr(agent, "memory_manager", None)).__name__)
print("\n=== SYSTEM PROMPT (chars) ===", len(agent.system_prompt or ""))
print("=== CONTRACT (chars) ===", len(HARNESS_CONTRACT))
