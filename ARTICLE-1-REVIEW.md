# Article 1 — evidence and publication review

**Draft:** [ARTICLE-1.md](ARTICLE-1.md), rewritten under
[ARTICLE-PLAN.md](ARTICLE-PLAN.md). This is a review log for the local draft,
not reader-facing article text. No paid model calls were made for this rewrite.

## What was checked

| Draft claim or example | Check | Result |
|---|---|---|
| The tested assembled agent exposed twelve registered tools | `poc/31_strands_surface.py` and `poc/results_strands_surface.json` | 12 names in the inspected 0.1.2 build. The inspector used a dummy API key and made no model call. This does not count native provider search as a registered tool. |
| Offloading left 9,928 versus 175,317 characters in conversation | `poc/10_offloading.py` and `poc/results_offloading.json` | Both rows present; metric is serialized conversation characters. The tool read was capped at 2,000 lines, so the draft explicitly avoids a whole-file claim. |
| Forced summarization left four versus fourteen messages | `poc/22_summarization.py` and `poc/results_summarization.json` | Both rows present after six facts and a follow-up question. The model window and threshold were reduced for the test. |
| A session resumed in another process | `poc/21_session_restart.py` and its result | Two earlier messages were restored before the second process asked; the arbitrary number and owner were recalled. A clean restart was tested, not crash recovery. |
| Memory brought a fact into a fresh conversation | `poc/08_memory.py` and its result | The test explicitly flushed memory, then a new agent with the same directory recalled the codeword and team. |
| Code mode could be bypassed by the model's choice of direct reads | `poc/results_codemode_diagnostic.json` | One instrumented bulky run recorded 40 direct reads and five programmatic-tool calls; the draft gives no pooled frequency or exact-score claim. |
| Built-in delegation kept trace markers out of the parent's history | `poc/07_subagent_isolation.py` and its result | Zero of 2,400 markers in the tested parent history, against 2,400 in the direct-read arm. No general confidentiality claim. |
| Monty blocked the attempted host operations | `poc/06_sandbox_boundary.py` and its result | Nine attempted accesses failed; control arithmetic returned 45. The draft limits the result to attempted paths and tested release. |
| The simulated deletion tool did not execute in the denied run | `poc/17_custom_tools.py` and its result | The lookup ran in a separate registration check without the policy. Under the policy, the deletion function's counter stayed zero and the agent reported a denial. The function only increments a counter and returns text; it deletes nothing. The path probe is described with its model-report limitation. |
| Skill and MCP examples behaved as described | `poc/09_skills.py`, `poc/16_mcp.py`, `poc/25_mcp_http.py` and results | The skill directory was explicitly configured; format markers appeared only with skills enabled. Fourteen namespaced MCP tools were discovered; a working server survived a broken peer; the tested HTTP tool answered. |
| Narrow Cedar configuration shown in the article builds | Constructed an agent with the article's options and `poc/agent.cedar` on `.venv-new`, using a dummy Anthropic key | Construction succeeded without calling the model. Requires the repository's Cedar dependency and running from the repository root. |

The current official [configuration reference](https://strandsagents.com/docs/user-guide/harness/reference/configuration/),
[programmatic-tool guide](https://strandsagents.com/docs/user-guide/harness/tools/programmatic-tool-calling/),
[interventions guide](https://strandsagents.com/docs/user-guide/harness/configure/interventions/),
and [production guidance](https://strandsagents.com/docs/user-guide/harness/production/)
were checked for the behavior described. The live documentation can change after the
tested releases; the method note names those releases. The article names its model
explicitly and does not repeat the old draft's default-model name.

## Earlier claims withheld from this draft

The old **4/20 versus 18/19** tally combines runs recorded through different scripts.
The provenance from each included run to a complete archived answer and service/value
grading is not transparent enough for a fresh audit. `02_context_economics.py` stores
only the final 400 characters plus a permissive substring flag. The revised draft
therefore makes no numerical accuracy comparison. This hold does not establish that
the historical tally is wrong; it keeps an unaudited number out of publication text.

The 0.1.2 **4/12 versus 10/12** replication is also withheld. In
`poc/results_small_crossover.json`, two code-mode rows score 5/6 and 1/6 on their saved
answer tails while the whole-answer substring flags say all six numbers appeared
somewhere in the response. The complete responses were not saved. The substring flag
does not prove the values were associated with the right services, and the truncated
tail cannot establish that they were wrong. The count needs complete-answer evidence
or a new, properly recorded run before being cited.

The small and bulky fixtures were generated independently: only one incident ID has
the same service and downtime in both current datasets. The draft describes them as
two workload shapes and does not attribute a cross-dataset difference solely to file
size. It also removes the invalid example that indexed `await read(...)` directly as
a parsed dictionary.

## Refinement review — 2026-09-24

Reviewed the draft for argument, pacing, reader prerequisites, and evidence scope.
The opening now states the practical benefit immediately. Removed references to the
old draft and the unfinished scoring audit from the reader-facing prose. The ending
now describes a concrete first evaluation using independently calculated totals,
complete answers, and recorded tool calls.

Clarified the boundaries between the code interpreter, tool execution environment,
and intervention policy. Read `poc/agent.cedar` directly: its read permission matches
the supplied path against `*/data/incidents/*`. The article now describes that exact
check and does not imply tested containment against alternate paths or symlinks.
No bypass experiment was performed and no framework defect is asserted. Also
identified the simulated deletion function and the separately configured skill
directory accurately. Summarization now states that both arms recalled the fact.

Rechecked the official SDK overview, programmatic-tool guide, and interventions
guide. The refined article contains 2,490 prose words using the prior counting
method (exclude fenced code and HTML comments; count link labels). Its twenty local
links resolve, both Python examples parse, and the examples' executable code is
unchanged from the previous review. No model calls were made.

## Remaining publication checks

The local editorial pass is complete. Before external publication, verify that
every linked result is included in the published repository and recheck wording
that depends on the release being named. Keep numerical accuracy claims in
Article 2's audit until complete answers or a fresh controlled run can support them.
