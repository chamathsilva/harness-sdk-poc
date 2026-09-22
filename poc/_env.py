"""Load .env and fail loudly if the API key is missing. No AWS involved."""
import os, pathlib, sys

def load():
    env = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
    # Make sure no stray AWS config can be picked up by a misconfigured run.
    os.environ.pop("AWS_PROFILE", None)
    return os.environ["ANTHROPIC_API_KEY"]


HAIKU = "claude-haiku-4-5-20251001"
MODEL = f"anthropic/{HAIKU}"


def assert_haiku(agent):
    """Hard guardrail: refuse to run if anything resolved to a non-Haiku model.

    The harness picks models in more places than the `model=` argument (web_fetch's
    summarizer, subagent tiers, memory extraction), so this inspects what actually
    got built rather than trusting the call site.
    """
    found = []

    def check(obj, where):
        cfg = getattr(obj, "get_config", None)
        if not callable(cfg):
            return
        mid = str((cfg() or {}).get("model_id", ""))
        if mid:
            found.append((where, mid))
            if "haiku" not in mid.lower():
                raise SystemExit(f"GUARD TRIPPED: {where} resolved to {mid!r}, not Haiku. Aborting.")

    check(getattr(agent, "model", None), "agent.model")
    for name in ("memory_manager", "context_manager"):
        sub = getattr(agent, name, None)
        check(getattr(sub, "model", None), f"{name}.model")
    print(f"[guard] models in use: {found}")
    return found
