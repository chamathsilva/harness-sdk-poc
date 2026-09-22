"""Does the summarize-and-stash mechanism actually fire?

Article 1 says older turns get summarized and filed away, with `retrieve_context` to
fetch them back. That came from reading `presets.py`, never from watching it happen.

Filling a 200k window to reach the default 70% trigger would be expensive, so this
shrinks the window the context manager measures against instead. That verifies the
MECHANISM (older turns collapse into a summary), not the default 0.7 threshold value.

A control run with context management off shows the history untouched.

Note on what "working" looks like: the early facts should still be *present* after
summarization. A summary that dropped them would be a bad summary. The signal is that
the message COUNT and history SIZE fall while the agent can still answer.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL, HAIKU

load()
from strands_harness import create_harness
from strands._context_manager.strategies.offload import Offload

# Distinctive facts, one per turn. If summarization works, the early ones should stop
# appearing verbatim in the message history while staying recoverable.
TURNS = [
    "Remember: the Helsinki datacentre uses cooling loop ZX-9.",
    "Remember: the on-call rota for March is owned by Tomas.",
    "Remember: the backup window starts at 02:15 UTC.",
    "Remember: the legacy billing job is named nightly-recon-v3.",
    "Remember: the staging database password rotates every 45 days.",
    "Remember: the incident bridge is room 4B.",
]
PROBE = "What is the name of the cooling loop in the Helsinki datacentre?"


def small_window_model(limit: int = 2000):
    """A Haiku model that *reports* a tiny context window.

    Conversation summarization triggers on `utilization` -- a fraction of the context
    window -- not on an absolute token count (`threshold` is what the tool-result
    strategies use). Rather than spend a fortune filling Haiku's real 200k window,
    shrink the window the context manager measures against.
    """
    from strands.models.anthropic import AnthropicModel
    return AnthropicModel(model_id=HAIKU, max_tokens=1024, context_window_limit=limit)


def build(managed: bool):
    kw = {}
    if managed:
        # Fires once the conversation passes 50% of a 2,000-token window, i.e. ~1,000
        # tokens. The six turns below come to roughly 900-1,100.
        kw["context_manager"] = {
            "strategies": [Offload.summarize("*").when(utilization=0.5, preserve_recent=2)]
        }
    else:
        kw["context_manager"] = False
    a = create_harness(model=small_window_model(), builtin_tools=[],
                       memory=False, session=False, skills=False,
                       builtin_plugins=[], **kw)
    assert_haiku(a)
    return a


def run(label, managed):
    agent = build(managed)
    for t in TURNS:
        agent(t)
    convo = json.dumps(agent.messages, default=str)
    answer = str(agent(PROBE))
    return {
        "label": label,
        "tools": sorted(agent.tool_names),
        "has_retrieve_context": "retrieve_context" in agent.tool_names,
        "messages_after_turns": len(agent.messages),
        "history_chars": len(convo),
        "first_fact_verbatim_in_history": "ZX-9" in convo,
        "summary_markers": [w for w in ("summar", "earlier conversation", "previously")
                            if w in convo.lower()],
        "still_answers_first_fact": "zx-9" in answer.lower(),
        "answer": answer[-250:],
    }


if __name__ == "__main__":
    out = []
    for label, managed in [("context management ON (forced low)", True),
                           ("context management OFF (control)", False)]:
        print(f"\n=== {label} ===", flush=True)
        try:
            r = run(label, managed)
        except Exception as e:
            r = {"label": label, "ERROR": f"{type(e).__name__}: {e}"[:400]}
        print(json.dumps({k: v for k, v in r.items() if k not in ("answer", "tools")}, indent=2),
              flush=True)
        out.append(r)
    pathlib.Path(__file__).with_name("results_summarization.json").write_text(json.dumps(out, indent=2))

    print("\n" + "=" * 76)
    print(f"{'run':<36}{'msgs':>6}{'chars':>9}{'1st fact kept':>15}{'recalls it':>11}")
    print("-" * 76)
    for r in out:
        if "ERROR" in r:
            print(f"{r['label']:<36}  ERROR: {r['ERROR'][:30]}")
            continue
        print(f"{r['label']:<36}{r['messages_after_turns']:>6}{r['history_chars']:>9,}"
              f"{str(r['first_fact_verbatim_in_history']):>15}{str(r['still_answers_first_fact']):>11}")
    print("=" * 76)
    print("Wanted: the managed run has FEWER messages and a SHORTER history than the\n"
          "control, and still answers the first fact. The fact itself should survive --\n"
          "it is carried in the summary.")
