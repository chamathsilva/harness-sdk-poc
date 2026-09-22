"""Is the sandbox really sealed, or does it just look sealed?

The article claims the sandbox "has no ability to touch files, the network, or other
programs -- those capabilities do not exist inside it". That sentence came from a
docstring. This tries to break out, directly, rather than taking it on faith.

We drive the sandbox tool ourselves instead of asking the model to, so the test is
deterministic: exactly this code runs, every time.
"""
import asyncio, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness

ESCAPES = {
    "open a file":            'print(open("/etc/hosts").read()[:40])',
    "import os":              'import os\nprint(os.listdir("/"))',
    "read env vars":          'import os\nprint(os.environ.get("ANTHROPIC_API_KEY"))',
    "spawn a process":        'import subprocess\nprint(subprocess.run(["id"], capture_output=True))',
    "open a socket":          'import socket\ns = socket.socket()\ns.connect(("example.com", 80))\nprint("connected")',
    "http request":           'import urllib.request\nprint(urllib.request.urlopen("http://example.com").status)',
    "import via __import__":  'm = __import__("os")\nprint(m.getcwd())',
    "escape via builtins":    'print(__builtins__.__dict__.get("open"))',
    "read own source file":   'print(open(__file__).read()[:40])',
    # control: this SHOULD work -- proves the sandbox is actually running our code
    "CONTROL: arithmetic":    'print(sum(range(10)))',
}


async def main():
    agent = create_harness(
        model=MODEL, effort="off",
        builtin_tools=["read", "programmatic_tool_caller"],
        memory=False, session=False, skills=False,
        builtin_plugins=[], context_manager=False,
    )
    assert_haiku(agent)
    results = {}
    for label, code in ESCAPES.items():
        try:
            out = agent.tool.programmatic_tool_caller(code=code, record_direct_tool_call=False)
            text = json.dumps(out, default=str)[:400]
            low = text.lower()
            blocked = ('"status": "error"' in low or "traceback" in low
                       or "not supported" in low or "unsupported" in low
                       or "is not defined" in low or "no module named" in low
                       or "unknown" in low or "denied" in low)
        except Exception as e:
            text, blocked = f"{type(e).__name__}: {e}"[:300], True
        results[label] = {"blocked": blocked, "response": text}
        mark = "BLOCKED" if blocked else "ALLOWED"
        print(f"{mark:>8}  {label}")
        print(f"          {text[:170]}")
    pathlib.Path(__file__).with_name("results_sandbox.json").write_text(json.dumps(results, indent=2))
    escaped = [k for k, v in results.items() if not v["blocked"] and not k.startswith("CONTROL")]
    print("\n" + "=" * 70)
    print("ESCAPES THAT SUCCEEDED:", escaped or "none")
    print("CONTROL ran:", not results["CONTROL: arithmetic"]["blocked"])
    print("=" * 70)


asyncio.run(main())
