# Final editorial plan

**Status:** Agreed with the author in this task. This is the authoritative publication
plan. Article 1 has a revised local draft and evidence review; external publication
remains a separate step.

This plan supersedes the publication sequence, titles, scope, and completion criteria
in [ARTICLE-SERIES.md](ARTICLE-SERIES.md). That file remains a historical record of
claim checks; its five-step rule for negative claims still applies. Historical
"verified" or "closed" labels do not override the evidence issues recorded below.

## Publication decision

Write **two standalone articles**, with a third dependent on additional evidence or a
complete working example. Publish the introduction first and cross-link the pieces
as they appear. Do not announce a numbered series or promise later articles.

The reader is a developer who understands agents and is deciding whether to evaluate
Strands Harness in a project. The editorial value is measured behavior, reproducible
examples, and clear configuration decisions. Explain features through the problems
they address and the consequences of their defaults.

Word counts below are editorial targets, not experimental measurements.

## Article 1 — the practical introduction

**Working title:** *Strands Harness in Practice: What It Handles and What You Still Control*

**Central question:** What work does adopting this harness save an engineer, and
which decisions remain theirs?

**Reader outcome:** Understand where the harness sits above the SDK, what it assembles,
how selected capabilities behaved in controlled tests, and what to configure for a
first evaluation.

**Length:** 2,200–2,800 words; aim for 2,500 words of prose.

The article should:

1. Introduce a small agent and the distinction between the assembled harness and SDK.
2. Explain working context, saved conversations, and long-term memory with selected
   observations and their limits.
3. Show how tools, code mode, and delegation change the way work is performed.
4. Explain host access, the code sandbox, and intervention policies together.
5. Finish with the choices to make for an initial project and a bounded verdict on
   whether the harness is worth evaluating.

The accuracy benchmark uses restricted tool sets and disables several default
features. Present it as a test of one capability; it does not measure the complete
default agent. Include a concise accuracy summary only after the relevant scores
are auditable. Keep detailed distributions, cost comparisons, and failure traces
for Article 2.

Include safety within Article 1. Do not offer a production-readiness verdict: these
experiments do not evaluate a deployed service, tenant isolation, operational
recovery, or production load.

The editorial brief, section budgets, evidence selection, and rewrite map are in
[ARTICLE-1-OUTLINE.md](ARTICLE-1-OUTLINE.md). The complete revised draft is
[ARTICLE-1.md](ARTICLE-1.md); its evidence audit is
[ARTICLE-1-REVIEW.md](ARTICLE-1-REVIEW.md). The previous draft is archived.

## Article 2 — the controlled experiment

**Working title:** *Tool Calls or Code Mode? A Controlled Strands Harness Experiment*

**Central question:** How does giving Haiku access to code mode change accuracy,
input volume, and variability on an aggregation task?

**Reader outcome:** Understand the mechanism, the observed trade-offs, and a method
for testing whether code mode helps their own workload.

**Length:** 1,800–2,400 words.

Cover the task and controls; how code holds intermediate tool results outside the
conversation; correctness and input-volume distributions; and runs in which the
agent returned to direct reads. Explain that tool calls can be batched in the
read-only arm: the experiment does not enforce one serial call per turn.

Keep conclusions specific to the tested model, versions, and tasks. Distinguish input
token volume from money: the repository's `billable_input` metric counts uncached
input, cache reads, and cache writes, but does not apply their different prices or
include output-token charges.

Before publishing numerical accuracy claims, repair the scorer and preserve full
answers. Regrade archived complete outputs where possible. If complete evidence is
unavailable, identify the unresolved rows and use a fresh, properly recorded
experiment for the affected claim. Do not overwrite historical results to make them
fit corrected fixtures or grading.

A frontier-model check remains optional and requires explicit approval under the
Haiku-only instruction. It is not a prerequisite for a clearly scoped Haiku article.

## Conditional future work

| Topic | What would justify an article |
|---|---|
| Constraining an agent's access | A reproducible example that tests the execution environment as well as tool policies, including allowed operations and denied operations. The existing code-sandbox probes alone are insufficient for an end-to-end isolation claim. |
| Multi-agent architecture | More trials and varied workloads, trustworthy task scoring, and a conclusion that survives noisy runs. The current five-run comparisons remain exploratory. |
| Strands versus Deep Agents | Equivalent live tasks, explicit configuration choices, and comparable correctness and usage accounting. The current static comparison is preparatory research. |

Memory, skills, MCP, tracing, and structured output are supporting material unless a
new experiment or substantial implementation produces a distinct reader benefit.
The deprecated structured-output method's cold-call behavior is a usage lesson;
avoid presenting it as a framework defect or the centerpiece of a new article.

## Evidence issues that take precedence over the old plan

| Issue | Evidence and required handling |
|---|---|
| Truncated answers are used for grading | `02_context_economics.py` saves only `answer_tail`; `26_small_crossover.py` grades that tail. Two code-mode rows have incomplete totals in the saved text. Their full-answer substring flags are not a reliable substitute for exact service/value grading. The reported 10/12 replication count needs revalidation; do not infer a replacement count. |
| Earlier graders are permissive | `02`, `14`, and `15` search for numeric substrings rather than verifying every requested service/value association. Audit any accuracy claim that depends on these graders. Keep task-completeness claims within what was actually checked. |
| The datasets are generated independently | Only 1 of 40 matching incident IDs has the same service and downtime in both current datasets. A/B arms share data within each dataset; small-versus-large comparisons do not isolate payload size alone. Correct "the same 40 records, now bulky" wording. A matched-size experiment would require new fixtures and results. |
| Old summaries conflicted with later findings | README's "all runs were correct" summary and the retracted "3 tools do no work" matrix row were corrected during the Article 1 rewrite. Older historical prose remains; use scripts, outputs, and the latest qualified findings rather than copying its claims. |
| The previous code-mode example omitted parsing | `read` returns tool content with numbered lines, not a parsed incident dictionary. The revised Article 1 replaces the invalid snippet with prose explaining the parsing step. |

The original accuracy tally also needs a transparent mapping from each included run
to its output and scoring method. The issue with `26` does not by itself establish
that the older tally is wrong; equally, its historical approval is not a fresh audit.

## Publication sequence and completion criteria

1. Refine Article 1's brief and outline, then revise its prose around the agreed
   question. Resolve the evidence issues for every measurement selected for it.
2. Check each retained claim against its script, output, tested version, and scope.
   Check technical examples against the tested API. Apply the existing five-step
   rule before publishing a negative claim.
3. Publish Article 1 when it stands alone, fits its budget, and has no unresolved
   claims in its publication text. Link the repository and state the Haiku and
   synthetic-task limitations. Do not claim every capability was tested under defaults.
4. Publish Article 2 after its grading and dataset descriptions are sound, its full
   outputs are retained, and all aggregate figures can be regenerated.
5. Select any third article based on a distinct question and sufficient new evidence.

## Reference points

- [Strands launch post](https://strandsagents.com/blog/introducing-strands-harness/)
  explains the assembled capabilities and vendor benchmarks. Our experiments do not
  reproduce those benchmark comparisons.
- [Programmatic tool calling](https://strandsagents.com/docs/user-guide/harness/tools/programmatic-tool-calling/)
  documents the distinction between code isolation and the tools' execution environment.
- [Production guidance](https://strandsagents.com/docs/user-guide/harness/production/)
  identifies configuration decisions for deployment; citing it does not make those
  deployments tested by this project.

These are source references, not evidence that the repository has rerun its
experiments against whatever version is currently published.
