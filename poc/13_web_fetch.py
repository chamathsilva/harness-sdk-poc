"""Does web_fetch really distil a page, or does it paste it into the conversation?

The article claims web_fetch "fetches it, strips it to text, and asks a small cheap
model to answer your specific question from it. A 10,000-word article comes back as
two sentences." That came from the README. Testing it against a long public page.

Note: this makes a request to Wikipedia, a third party. Public page, no local data sent.
"""
import json, pathlib, sys, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness

URL = "https://en.wikipedia.org/wiki/Apollo_11"
QUESTION = "On what date did the Apollo 11 lunar module land, and who stayed in orbit?"


def raw_page_size():
    req = urllib.request.Request(URL, headers={"User-Agent": "harness-sdk-poc/1.0 (evaluation)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return len(r.read())


def main():
    size = raw_page_size()
    print(f"raw page: {size:,} bytes (~{size//4:,} tokens if pasted whole)")

    agent = create_harness(model=MODEL, effort="off", builtin_tools=["web_fetch"],
                           memory=False, session=False, skills=False,
                           builtin_plugins=[], context_manager=False)
    assert_haiku(agent)
    print(f"tools: {sorted(agent.tool_names)}")

    result = agent(f"Using web_fetch on {URL}, answer: {QUESTION}")
    text = str(result)
    convo = json.dumps(agent.messages, default=str)

    # Wikipedia boilerplate that WOULD be present if the page were pasted wholesale.
    markers = ["Jump to content", "Retrieved from", "Categories:", "[edit]", "navbox"]
    present = [m for m in markers if m in convo]
    correct = ("july 20" in text.lower() or "20 july" in text.lower()) and "collins" in text.lower()

    print("\n" + "=" * 72)
    print(f"raw page bytes         : {size:,}")
    print(f"conversation chars     : {len(convo):,}")
    print(f"ratio                  : {size/max(len(convo),1):.1f}x smaller than the page")
    print(f"page boilerplate found : {present or 'none'}")
    print(f"answered correctly     : {correct}")
    verdict = ("DISTILLED, NOT PASTED" if len(convo) < size / 3 and not present
               else "PAGE APPEARS TO BE IN CONTEXT")
    print(f"VERDICT: {verdict}")
    print("=" * 72)
    print(f"\nanswer: {text[:400]}")

    pathlib.Path(__file__).with_name("results_web_fetch.json").write_text(json.dumps({
        "url": URL, "raw_page_bytes": size, "conversation_chars": len(convo),
        "boilerplate_markers_found": present, "answered_correctly": correct,
        "verdict": verdict, "answer": text[:800],
    }, indent=2))


main()
