# Article series plan

What each article is for, what backs it, and what must happen before it ships.

**Last updated:** 2026-09-22 · Start with [AGENTS.md](AGENTS.md). Evidence lives in
`FINDINGS.md`, `FINDINGS-MULTIAGENT.md`, `FINDINGS-EXTENDING.md`.

---

## The series in one paragraph

**Article 1 is the goal:** a hands-on introduction to Strands Harness. It covers what
the framework is, what comes in the box, and how each part behaves when you actually run
it. Every capability is backed by a measurement, not a paraphrase of the README.
Articles 2–4 each take one section of article 1 and go deep on it.

The link between them is one pattern the measurements kept turning up: **agent
reliability comes from taking discretion away from the model.** That means code instead
of mental arithmetic (article 2), structure instead of model-chosen delegation
(article 3), and policy and schemas instead of trust (article 4). Article 1 names the
pattern once, near the end. It does not lead with it.

| # | Working title | Role | Status |
|---|---|---|---|
| **1** | *Strands Harness, Hands-On: What AWS's New Agent Harness Actually Does* | Flagship introduction | Evidence ~90%; the draft needs restructuring |
| 2 | *Stop Letting the Model Do the Maths* | Deep dive: code mode | Evidence ready |
| 3 | *Multi-Agent Systems Don't Make Agents Faster. They Make Them Predictable.* | Deep dive: multi-agent | Evidence ready, n=5 |
| 4 | *A Validated Object Is Not a Correct One* | Deep dive: extending it safely | Evidence mostly ready |
| 5 | *(optional)* Frontier-model re-run | Checks whether 1–4 hold beyond Haiku | Parked: needs approval |

**Order:** article 1 first and on its own. Then 2 → 3 → 4, because article 3's key
finding (the 3.1M-token run) has the same cause as article 2's fallback, so it reads
better once article 2 has explained that failure. Each article still stands alone.

---

## Standing rule: no negative claim ships unchecked

Nothing gets called broken, missing, misleading or a bug until it has passed all five
steps below. The rule covers every article, including negative wording in passing
("does no work", "a wart", "a trap").

1. **Current release.** Check that a newer version hasn't changed it. If one has,
   reproduce on that version.
2. **Fresh reproduction.** Reproduce it now, on its own, and don't rely on an old log.
3. **Source.** Read the implementation. Is this the intended behaviour?
4. **Docs.** Check the README, docstrings and changelog. Is it documented?
5. **Our misuse.** Run the documented, correct usage as a control, and search upstream
   issues (`gh issue list -R strands-agents/harness-sdk --search ...`).

Every claim then gets one verdict, and the verdict limits the wording:

| Verdict | Allowed wording |
|---|---|
| **Confirmed defect** | May be called a bug or limitation, with the reproduction |
| **Documented behaviour** | Described neutrally, as a gotcha worth knowing. Never "broken" |
| **Our misuse** | Dropped, or turned into a usage tip |
| **Fixed upstream** | Dropped, or noted with the version that fixed it |
| **Unresolved** | Not published |

Always use the weakest wording the evidence supports.

---

## Article 1 — the flagship

**Working title:** *Strands Harness, Hands-On: What AWS's New Agent Harness Actually Does*

**Objective:** the reader leaves knowing what it is, what's in the box, how each part
behaves when run, and whether to try it this week.

**Reader:** engineers deciding whether to look at it. Assumes they know what an agent
is. Assumes no knowledge of Strands.

**Length:** 3,000–3,500 words. One number per capability. Depth goes to articles 2–4.

### Outline, with the proof point for each section

| § | Section | Proof point | Source | Status |
|---|---|---|---|---|
| 1 | **What it is.** Strands harness vs the Strands Harness SDK (naming per the launch post); vendor's positioning and benchmark claims (G8); one `create_harness()` call; what the defaults switch on; where it sits in the Strands stack; released 2026-09-21, Apache-2.0 | Inspection of one call: 12 tools, context and memory managers, session, cache config, the 1,665-char contract | `01` | Verified (static) |
| 2a | Built-in tools and **code mode** | 4/20 vs 18/19 perfect runs | `04`, `05` | Verified |
| 2b | **Two sandboxes**: Monty for code mode, and the execution environment for `shell`/files | Monty: escape attempts contained, with a control. Execution environment: host by default, Docker/SSH available (G7) | `06`, source | Monty verified; environment source-read |
| 2c | **Context management** | Offloading 9,928 vs 175,317 chars; summarization 14 → 4 messages | `10`, `22` | Verified |
| 2d | **Memory and sessions** | Memory reaches a new conversation; a session survives a real process restart | `08`, `21` | Verified |
| 2e | **Skills** | Invented house format followed only when the folder is present | `09` | Verified w/ control |
| 2f | **Delegation** | Subagent isolation, 0 vs 2,400 leaked markers; `as_tool()`, `make_subagent()` | `07`, `23` | Verified |
| 2g | **Multi-agent** (teaser for article 3) | `Graph` / `Swarm` exist and work; one line on predictability | `14`, `24` | Verified, n=5 |
| 2h | **Extensibility** | Custom `@tool` reachable in the sandbox; MCP over stdio and HTTP | `16`, `17`, `25` | Verified |
| 2i | **Safety controls** | Cedar blocks a call inside the sandbox; `"smart"` and plain-English policies gate correctly | `03`, `17`, `19` | Verified w/ control |
| 3 | **What surprised me** | N2, N5 (approved wording below); N3 if not used in §2a | §11 | N2 ready; N5 after its control |
| 4 | **Before you ship it** | N6 (approved wording below) | §11 | Ready |
| 5 | **Verdict** | Who it is for; which defaults to change first | — | Written last |
| 6 | **Method box** | Haiku 4.5, sample sizes, repo link, frontier caveat | — | Ready |

### Critical-claim register — phase 1 done (static checks on 0.1.2 / 1.57.0)

Full evidence is in `FINDINGS.md` §11. The **approved wording** column is the only
wording the draft may use.

| ID | Verdict | Approved wording | Where it goes |
|---|---|---|---|
| **N1** | **Wrong** (our framing) | "Two of the twelve fetch back content the harness moved out of the context window; a third searches long-term memory. Each arrives with the feature that needs it." | §1 what it is |
| **N2** | **Confirmed defect, known upstream (#3546)** | "On the Anthropic API, `totalTokens` leaves out cached tokens, a known open issue (#3546). For cost, add `cacheReadInputTokens` and `cacheWriteInputTokens`." | §3 surprises |
| **N3** | **Confirmed**: model behaviour, not framework | "On our task, Haiku abandoned code mode and read files itself in 2 of 24 runs. Those runs cost about 17× the median, and one still got every figure right." | §2a, detail in article 2 |
| **N4** | Pending phase 2 | Until then: "on small inputs the overhead can outweigh the saving" | §2a |
| **N5** | **Documented behaviour**; fairness control pending | "The deprecated `agent.structured_output()` makes one model call over the conversation so far and runs no tools, as its docstring says. Asked cold to analyse files, it returned schema-valid objects full of invented figures (3/3). The replacement, `structured_output_model=`, ran the tools and got 6/6." | §3 surprises, detail in article 4 |
| **N6** | **Confirmed and documented** | "Out of the box, `shell` and the file tools run on your machine with your privileges, and no call is gated. The SDK is blunt about it: the default environment is called `NotASandboxLocalEnvironment`. A Docker or SSH sandbox, or an interventions policy, is one argument away." | §4 before you ship |
| N7a | Documented design | Tip only: "`read` numbers its lines so the model can cite `path:line`; code that parses file contents strips them" | Article 2 |
| N7b | Documented | Tip only: "`read` takes absolute paths and reads files; listing is `shell`'s job" | Article 2 |
| N7c | **Our misuse** | **Dropped** | — |
| N7d | Documented | Optional: "web search is the provider's native tool where one exists, or Exa's hosted search on any model if you opt in" | §2 tour, one line |
| **N8** | Softened | "Turning reasoning on did not close the gap" | §2a |

**What phase 1 changed:** N1 and N7c are gone. N5 and N7a/b/d moved from flaw to
documented behaviour. N2 moved the other way: it's a real defect, already reported
upstream. G5 corrected a number we'd been carrying: the default summarizes at **85%**,
not 70%. The sandbox section needs splitting in two (G7).

### Gaps — status after phase 1

| ID | Status | For the article |
|---|---|---|
| G1 observability | Source read; **one run pending** | "Spans for the model loop, tool calls and delegation; set `OTEL_TRACES_EXPORTER`." Say so only after the run |
| G2 providers | **Closed** | "Seven provider prefixes in the source; I ran two" |
| G3 version | **Closed**: 0.1.2 / 1.57.0 | Method box names the versions. Re-run `16`, `17`, `22`, `25` on 0.1.2 |
| G4 TypeScript | **Closed** | Existence only: `@strands-agents/harness` 0.1.1, Node ≥22 |
| G5 summarization | **Closed, corrected** | "Summarizes above 85% of the window; truncates tool results over ~1,500 tokens" |
| G6 Strands CLI | New; untested | Existence and `/export` only, unless tested |
| G7 two sandboxes | New | §2b must separate **Monty** (code mode, sealed, verified) from the **execution environment** (host by default) |
| G8 vendor benchmarks | New | Cite the launch post's 28% and 77% as the vendor's claims; say we didn't reproduce them |

### Phase 2 checklist (small Haiku runs, on 0.1.2)

1. **N5 fairness control:** call `structured_output()` *after* the agent has read the data.
2. **N2 live capture:** one cached run on 0.1.2 printing all four usage fields.
3. **G1:** one run with `OTEL_TRACES_EXPORTER=console`, confirming model and tool spans.
4. **Re-run on 0.1.2:** `16` MCP stdio, `17` custom tools, `22` summarization, `25` MCP HTTP.
5. **N4:** raise small-data code mode from n=7 to n≥12. The one costly item; run it in the background.
6. *Optional:* N8 (raise n), G6 (CLI smoke test with Haiku).

### Out of scope for article 1

The detail goes to the follow-ups. Article 1 keeps one sentence each:
- The effort/reasoning confound and the cost crossover → article 2
- Variance, the 3.1M-token run, plain `Agent` vs harness nodes → article 3
- The full structured-output trap, MCP config detail, the production checklist → article 4

### Definition of done

1. Every register entry N1–N8 has a verdict and approved wording. *(Phase 1: all but N4 and N5's control.)*
2. G1–G8 are closed or scoped to existence-only wording.
3. The draft is restructured into the tour above, at ≤3,500 words.
4. **Fact-check pass:** every number in the draft is traced to a row in `FINDINGS.md`
   §7, and the one accuracy tally (18/19, or 22/23 across all graded runs) is used
   consistently.
5. Haiku caveat and method box are present.
6. The draft is exported into the repo as Medium-ready markdown.

---

## Article 2 — code mode deep dive

**Working title:** *Stop Letting the Model Do the Maths*

**Objective:** when to use code mode, what it costs, and how to guard against the
model falling back to reading files itself.

**Content and evidence:**
- **Accuracy:** 4/20 perfect vs 18/19 (`04`, `05`). Failure is silent: it names the
  right worst service while getting the totals wrong by 50–100.
- **The effort confound:** reasoning on did not close the gap (N8 applies).
- **Cost crossover:** ~3× dearer on 16 KB, ~3.7× cheaper on 210 KB. The small-data arm
  needs n≥12 (N4).
- **Fallback:** 2/24 abandoned the sandbox, median 469,484 vs 26,650. Of the two, one
  scored 0/6 and one 6/6: reliably expensive, not reliably wrong.
- **Guardrails:** exact paths, and a prompt test for fallback. *Not yet tested.*

**Missing:** a guardrail experiment. Does any prompt or configuration measurably cut the
fallback rate?

---

## Article 3 — multi-agent deep dive

**Working title:** *Multi-Agent Systems Don't Make Agents Faster. They Make Them Predictable.*

**Objective:** a decision guide for choosing between one agent, `Graph`, `Swarm` and
`subagent`.

**Evidence, all n=5:**
- **Sequential task (`14`):** all four correct every run. Median vs single: graph
  0.92×, swarm 1.14×, subagent 2.78×. Best-to-worst spread: graph 2.2×, single 4.4×,
  swarm 4.0×, subagent **18.6×** (worst 651,935).
- **Fan-out over bulky shared data (`15`):** the graph's median is 4.88× the cost and
  1.52× the wall time (415,530 / 46.7s vs 85,096 / 30.7s). But the single agent had a
  **3,122,738**-token run, a 119× spread, against the graph's 6.6×. Trial-1 branch
  times sum to 58.9s within a 32.4s wall, so parallelism happened.
- **Root cause of the outlier:** 42 direct reads against 2 in the cheap runs. That's
  article 2's fallback.
- **Isolation:** 0 vs 2,400 leaked markers. A child inherits the parent's policy and
  cannot exceed its tools (`07`, `11`, `12`).
- **Node choice:** a harness agent asked to classify wrote 149 words; a plain `Agent`
  replied `URGENT`. Conditional edges route both ways, and nested graphs work (`24`).

**Critical claims needing the five-step check before drafting:**
- "Harness agents make poor narrow nodes": is `HARNESS_CONTRACT` the cause, or
  something else in the preset?
- The per-node cost attribution

**Missing:** heterogeneous models per node (needs non-Haiku approval), a task larger
than one context window, cycles, A2A.

---

## Article 4 — extending it safely

**Working title:** *A Validated Object Is Not a Correct One*

**Objective:** a practical guide to plugging your own tools, MCP servers and skills in
without losing control of them.

**Content and evidence:**
- **Custom `@tool`:** registered, reachable inside the sandbox as `async`, blocked by
  Cedar, with a counter proving it never executed (`17`).
- **MCP:** 14 tools from one stdio server, namespaced; a broken server is isolated
  (`16`). Streamable HTTP works with transport auto-detected or explicit (`25`).
- **Skills:** followed only when present (`09`). `web_fetch` compressed a page 791×
  with the answer correct (`13`).
- **Interventions:** `"smart"` and plain-English policies gated correctly, with a
  control (`19`).
- **Structured output:** `structured_output_model=` got 6/6. The deprecated route is
  the hook, but only in whatever form N5's check allows.

**Missing:** colliding tool names across servers, `mcp_router` (new in 1.57.0),
`tool_filters`, OAuth MCP, and skills with bundled scripts.

---

## Article 5 — optional frontier-model re-run

Every number is Claude Haiku 4.5. Articles 2 and 3 lean hardest on Haiku's behaviour:
the arithmetic gap and the sandbox fallback. Whether a frontier model fails the same
way decides whether this is a "small models need scaffolding" story or a general one.
Any of the three outcomes is publishable. **Parked under the Haiku-only instruction;
needs explicit approval.**

---

## Title alternatives (kept for later)

- **1:** *The Hard Part of AI Agents Was Never the AI* (the old thesis title; might
  suit article 2).
- **2:** *Your Agent Can't Add Up — And That's Fixable*
- **3:** *The Most Predictable Agent Is the One That Decides Least* · *I Measured Four
  Agent Architectures*. **Retired:** ~~*Your Multi-Agent System Is Probably Just
  Expensive*~~, disproven at n=5 (graph 0.92×). *One Agent Run Cost Me 3.1 Million
  Tokens* is rejected because it rests on n=1.
- **4:** *It Validated. It Was Also Entirely Made Up.* (depends on N5's verdict).
