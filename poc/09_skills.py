"""Does dropping a folder on disk actually teach the agent something?

The article claims a skill is just a folder with a SKILL.md, found automatically, with
only its name and description in context until it is needed. Test: invent a house
style no model would produce on its own, put it in a skill, and see whether the agent
discovers and follows it -- without being told the skill exists.
"""
import json, pathlib, shutil, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _env import load, assert_haiku, MODEL
load()
from strands_harness import create_harness

SKILLS = pathlib.Path(__file__).parent / ".skills_test"
MARKER_OPEN, MARKER_CLOSE = "INCIDENT BRIEF //", "FILED UNDER:"

SKILL_MD = f"""---
name: incident-brief
description: The house format for summarizing any incident record. Use whenever asked to summarize or describe an incident.
---

# Incident brief format

When summarizing an incident, you MUST follow this house style exactly:

1. Begin the summary with the literal text `{MARKER_OPEN}` followed by the incident id.
2. Give exactly one sentence describing what happened.
3. End with the literal text `{MARKER_CLOSE}` followed by the service name in UPPERCASE.

Never deviate from this format. It is what our on-call tooling parses.
"""

INCIDENT = pathlib.Path(__file__).parent.parent / "data" / "incidents" / "INC-1001.json"
# Note: the prompt never mentions the skill, a format, or the markers.
TASK = f"Summarize the incident in {INCIDENT}."


def main():
    if SKILLS.exists():
        shutil.rmtree(SKILLS)
    d = SKILLS / "incident-brief"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(SKILL_MD)
    print(f"wrote {d/'SKILL.md'}")

    for label, skills in [("skills ON", str(SKILLS)), ("skills OFF (control)", False)]:
        agent = create_harness(model=MODEL, effort="off", builtin_tools=["read"],
                               memory=False, session=False, skills=skills,
                               builtin_plugins=[], context_manager=False)
        assert_haiku(agent)
        print(f"\n=== {label} ===")
        print(f"tools: {sorted(agent.tool_names)}")
        answer = str(agent(TASK))
        followed = MARKER_OPEN in answer and MARKER_CLOSE in answer
        print(f"followed house format: {followed}")
        print(f"answer: {answer[:240]}")
        results[label] = {"has_skills_tool": "skills" in agent.tool_names,
                          "followed_format": followed, "answer": answer[:600]}

    print("\n" + "=" * 70)
    on, off = results["skills ON"], results["skills OFF (control)"]
    print(f"with skills   : format followed = {on['followed_format']}  (skills tool present: {on['has_skills_tool']})")
    print(f"without skills: format followed = {off['followed_format']}")
    print(f"VERDICT: {'SKILL WAS DISCOVERED AND APPLIED' if on['followed_format'] and not off['followed_format'] else 'INCONCLUSIVE'}")
    print("=" * 70)
    pathlib.Path(__file__).with_name("results_skills.json").write_text(json.dumps(results, indent=2))


results = {}
main()
