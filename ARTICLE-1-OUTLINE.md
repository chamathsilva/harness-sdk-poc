# Article 1 — refined brief and outline

**Plan:** [ARTICLE-PLAN.md](ARTICLE-PLAN.md) is the agreed publication plan.
**Status:** The brief guided a complete local rewrite; section budgets and evidence
selection are recorded here for review.
**Draft:** [ARTICLE-1.md](ARTICLE-1.md) is the revised article.
The previous outline is preserved in
[archive/ARTICLE-1-OUTLINE-PREVIOUS.md](archive/ARTICLE-1-OUTLINE-PREVIOUS.md).

## Title, subtitle, and promise

**Working title:** *Strands Harness in Practice: What It Handles and What You Still Control*

**Proposed subtitle:** *A practical look at its tools, context, memory, and permissions,
with experiments behind the advice.*

**Central question:** What work does adopting this harness save an engineer, and
which decisions remain theirs?

**Editorial thesis:** Strands assembles several pieces an agent application needs:
tools, instructions, context management, and persistence. An engineer still chooses
the task, the data and tools it may access, how state should persist, and how to judge
whether the result is correct. Selected experiments make those choices concrete.

This is a practical introduction for developers who know what an agent is but have
not used Strands. It should help them decide what to try and what to measure in a
first evaluation. It does not establish suitability for their production workload.

## Narrative and opening

Follow the work through an agent: it starts with tools and instructions, gathers
information, manages growing context, carries state between runs, and acts within
the authority it has been given. Explain each capability when that progression
makes it useful. Keep the incident-analysis task as a recurring example, while
identifying the memory, skills, and policy tests as separate experiments.

Open with the engineering question, then introduce the product. A proposed opening:

> Give an agent a folder of incident reports and ask which service lost the most time.
> The request sounds small. The agent still has to find the files, work through their
> contents, calculate the totals, and return an answer you can check. If you want it to
> continue tomorrow, something also has to preserve its state. And before it starts,
> you need to decide which files and commands it may use.
>
> Strands Harness assembles much of that machinery through `create_harness()`. I used
> synthetic incident data and focused tests to examine what the assembled agent gives
> you, how selected parts behave, and which decisions remain yours.

This is an opening proposal, not a new experimental result. It does not say the
aggregation benchmark exercised the complete default configuration.

## Section plan and word budget

Budgets are editorial estimates for prose, headings, and tables; exclude code and
internal drafting comments. Target 2,500 words, within the agreed 2,200–2,800 range.

| Section | Reader question | Words |
|---|---|---:|
| Opening | What will this evaluation help me decide? | 150 |
| 1. What one call assembles | Where does the harness fit, and what do I get? | 350 |
| 2. What happens as work accumulates | How are context and persistent state handled? | 450 |
| 3. How it gets the work done | What do code mode and delegation change? | 450 |
| 4. What it can touch | Which actions and resources have I authorized? | 450 |
| 5. Making it useful for my task | How do I add my instructions and capabilities? | 300 |
| 6. How I would start evaluating it | What should I configure and verify first? | 250 |
| Method note | How far do these observations extend? | 100 |
| **Total** | | **2,500** |

### 1. What one call assembles

Distinguish the assembled harness from the SDK below it. Show one short Python
example with the model explicitly named. Use a task tied to the incident files;
label any path the reader must replace. Explain that enabled shell and file tools
have host access before inviting the reader to execute a default-agent example.

Briefly cover tools, the built-in behavioral instructions, context management,
sessions, and memory. Explain what the user supplies. Compress the full tool
inventory into a few functional groups if a table helps.

The original inspection script reports plugins through an attribute that does not
exist; do not carry its empty list forward as evidence that plugins are absent.
Use the corrected findings and verify the selected example against the tested version.

Provider lists, TypeScript, and the CLI receive at most one short paragraph. Their
existence does not imply tested parity. Avoid a second install walkthrough.

### 2. What happens as work accumulates

Distinguish four things: the active conversation, offloaded content and summaries,
a saved session, and memory carried into a new conversation. Skills are instructions
and belong in section 5 rather than being described as another kind of memory.

Use a compact version of the existing desk metaphor. Explain why selected tool
results can be replaced with previews and later retrieved. One offloading measurement
can illustrate the mechanism, with the read limit and unit made explicit.

Explain session recovery through the two-process test. Describe memory extraction
with the invented-fact experiment and its background-work caveat. This proves recall
in that test, not reliable retention of every fact or crash-safe persistence.

Summarization can be described briefly. If its 14-to-4 message observation is used,
say the trigger was forced. Do not imply the default threshold was observed under
a naturally filled context window. Web-fetch compression is optional and should be
cut before adding another measurement to this section.

### 3. How it gets the work done

Explain that ordinary tool calls may be batched. In code mode, model-written code
calls tools, processes their results locally, and prints the information returned
to the model. The distinction is where orchestration and intermediate data live.

Describe the incident task, the two restricted tool sets, and the disabled features.
Include one audited accuracy comparison when available. The rewrite must not reuse
the historical 4/20 versus 18/19 tally or the 4/12 versus 10/12 replication line
without checking the supporting rows and their grading provenance. Do not replace
the disputed replication count by assuming the missing text was correct.

Explain one observation already visible in the saved tool metrics: having code mode
available did not force the model to stay in it; some runs made dozens of direct
reads. Keep the detailed cost table, pooled fallback rate, and outlier analysis for
Article 2. A concise input-volume caveat is enough here.

Introduce delegation as a way of keeping a helper's work out of the parent's
conversation. State the isolation experiment's scope. Mention Graph and Swarm as
SDK options only if needed to locate them; omit claims of general superiority or
predictability from the small architecture sample.

### 4. What it can touch

Explain the three boundaries together:

- Monty constrains the model-written program used by code mode.
- The execution environment determines where the called tools operate; host execution
  and a separately configured OS sandbox are different arrangements.
- Interventions decide whether a tool call may proceed.

Use one simple flow diagram if it makes the path clearer:
model -> direct tool call or code-mode tool call -> policy -> tool -> execution environment.
Show the code interpreter's boundary separately from the tools' execution boundary.

Anchor the policy explanation in the allowed and denied path test and the custom-tool
execution counter. Describe what those probes observed. The path test's result is
interpreted from model prose, so inspect its actual tool evidence before treating it
as conclusive; the counter test supplies a stronger side-effect observation.

Do not portray successful probes as a comprehensive security assessment. State that
Docker/SSH execution environments were not tested in this project. Scope inheritance
claims to the built-in delegation path actually exercised, rather than every way an
agent can be wrapped as a tool.

Give a concrete configuration choice for a first project. Any policy example must
match the file/tool paths used in the article. If interactive approval is shown,
account for its documented behavior inside code mode: it cannot prompt there and
the gated call raises an error. Avoid suggesting all intervention modes compose
freely or that a policy alone supplies OS isolation.

### 5. Making it useful for my task

Show how `instructions` and one custom tool adapt the harness to a domain. Explain
that granting a tool grants its underlying capability, so its access belongs in the
same review as built-in tools.

Keep skills and MCP concise: the house-format test demonstrates instruction
discovery with a control; the MCP experiments demonstrate server integration and
the observed failure isolation. Namespacing reduces collisions, but the project has
not tested all collision cases. Do not say names "can't collide."

Mention supported structured output as a way to obtain a validated object. Keep
schema validity separate from factual correctness. The cold-call behavior of the
deprecated method can be omitted; it would interrupt this article's progression.

### 6. How I would start evaluating it

Finish with an actionable, bounded recommendation: select a model explicitly;
choose tools and access appropriate to a small task; decide where sessions and
memory belong; capture usage and outputs; compare the answer with known truth.
Tracing can appear here as a means to inspect behavior, without a separate feature tour.

Describe the harness as worth evaluating when its assembled capabilities fit the
project. Explain that the SDK provides room for more explicit construction. Avoid
claims that one choice is universally safer or better, or that a release's age alone
establishes production readiness.

The closing should answer the original question about engineering work saved and
decisions retained. A link to Article 2 can be added once it is published; the first
article must deliver its own conclusion.

### Method note

Name the tested package versions, Haiku 4.5, the reasoning setting, and synthetic
fixtures. Distinguish default inspection, controlled component tests, source reads,
and the restricted benchmark. Link the code and results. State that vendor benchmarks
and production deployments were not reproduced. Use a total run count only if its
constituent runs can be enumerated.

## Evidence selection for the rewrite

These are candidates to trace again, not newly certified results.

| Candidate | Existing source | Required qualification |
|---|---|---|
| Assembled capabilities | `01`, `31`; corrected findings | Tested versions; correct the inspection artifact about plugins. |
| Offloading reduces stored conversation size | `10`, `results_offloading.json` | Character counts, not dollars or tokens; `read` capped the source at 2,000 lines; do not attribute everything to one retrieval tool. |
| Summarization compacts history | `22`, `results_summarization.json` | Forced trigger; mechanism test, not a live verification of the default threshold. |
| Session resumes across processes | `21`, `results_session_restart.json` | Clean process restart; no crash-recovery or concurrent-session claim. |
| Memory reaches a new conversation | `08`, `results_memory.json` | Invented fact, shared memory location, extraction allowed to finish. |
| Code-mode accuracy | `02`, `04`, `05`, `26` and extra recorded runs | Publication hold on exact tallies until provenance and scoring are checked. |
| Agent returns to direct reads | Recorded tool calls in code-mode results | Availability differs from actual use; reserve pooled rates for Article 2. |
| Delegate keeps bulk out of parent context | `07`, `results_subagent.json` | The marker experiment, not a universal confidentiality boundary. |
| Code sandbox and tool policies | `03`, `06`, `11`, `12`, `17`, `19` | Controls and side effects; no untested OS-isolation claim. |
| Tools, MCP, and skills extend the agent | `09`, `16`, `17`, `25` | Only the exercised configurations; collision/OAuth coverage remains open. |
| Supported structured output | `20`, `27` | Validity alone does not establish truth. |
| Traces aid inspection | `29`, `results_tracing.json` | Explicit exporter setup in the tested version. |

## What changes from the existing draft

| Existing material | Rewrite decision |
|---|---|
| Launch statistics and vendor comparisons in the opening | Replace with the engineering question; retain brief source attribution later if useful. |
| Long definition of a harness | Compress into the explanation of the assembled agent and SDK. |
| Twelve-tool inventory and long prompt quotations | Compress into capabilities and instructions relevant to the reader's task. |
| The desk; memory and sessions | Bring together while preserving their distinct functions. |
| Extended accuracy, cost, and fallback narrative | Keep one checked finding and the mechanism; move the full experiment to Article 2. |
| Code that indexes `await read(...)` as an incident dictionary | Replace with a verified parsing example or prose; the current snippet skips the actual return format. |
| Multi-agent cost/variance teaser | Remove the promised follow-up and any general predictability claim. |
| Safety discussion repeated in several places | Consolidate into section 4 with clear boundaries and observed controls. |
| Skills grouped as a third kind of memory | Move to task customization. |
| Deprecated structured-output story | Omit or retain as a short usage note only if it serves the section. |
| Production recommendations and broad model claims | Replace with a scoped recommendation for an initial evaluation. |
| Closing thesis about taking every decision away from models | Replace with the practical answer: what is assembled and what the developer controls. |

## Publication checks

The rewrite is complete. [ARTICLE-1-REVIEW.md](ARTICLE-1-REVIEW.md) records the
evidence audit and what remains for external publication. In particular:

- Resolve scoring for every accuracy number selected; otherwise omit that numerical
  claim rather than presenting an unresolved score as established.
- Describe independently generated datasets accurately and make the benchmark's
  restricted configuration explicit.
- Verify code examples and current documentation against the named tested version;
  distinguish newly sourced facts from historical measurements.
- Trace each included observation to the actual output and its control, with the
  five-step rule applied to negative claims.
- Keep the text self-contained within 2,200–2,800 words, with one complete conclusion
  and no dependency on future articles.
- Review the rewrite locally before deciding whether to update the external working
  document. The saved external draft is the provenance of the existing text, not
  evidence that this revised outline has already been applied there.
