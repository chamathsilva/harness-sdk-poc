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
| 1 | **What it is.** Agent loop vs harness layer; one `create_harness()` call; what the defaults switch on; where it sits in the Strands stack; released 2026-09-21, Apache-2.0 | Inspection of one call: 12 tools, context and memory managers, session, cache config, the 1,665-char contract | `01` | Verified (static) |
| 2a | Built-in tools and **code mode** | 4/20 vs 18/19 perfect runs | `04`, `05` | Verified |
| 2b | **Sandbox** | Escape attempts contained, with a control | `06` | Verified |
| 2c | **Context management** | Offloading 9,928 vs 175,317 chars; summarization 14 → 4 messages | `10`, `22` | Verified |
| 2d | **Memory and sessions** | Memory reaches a new conversation; a session survives a real process restart | `08`, `21` | Verified |
| 2e | **Skills** | Invented house format followed only when the folder is present | `09` | Verified w/ control |
| 2f | **Delegation** | Subagent isolation, 0 vs 2,400 leaked markers; `as_tool()`, `make_subagent()` | `07`, `23` | Verified |
| 2g | **Multi-agent** (teaser for article 3) | `Graph` / `Swarm` exist and work; one line on predictability | `14`, `24` | Verified, n=5 |
| 2h | **Extensibility** | Custom `@tool` reachable in the sandbox; MCP over stdio and HTTP | `16`, `17`, `25` | Verified |
| 2i | **Safety controls** | Cedar blocks a call inside the sandbox; `"smart"` and plain-English policies gate correctly | `03`, `17`, `19` | Verified w/ control |
| 3 | **What surprised me** | The critical claims N1–N8 below, **only after each passes the double-check** | — | **Pending** |
| 4 | **Before you ship it** | Default tool set and intervention state (N6) | — | **Pending** |
| 5 | **Verdict** | Who it is for; which defaults to change first | — | Written last |
| 6 | **Method box** | Haiku 4.5, sample sizes, repo link, frontier caveat | — | Ready |

### Critical-claim register — every entry needs the five-step check

These are the claims article 1 would currently make that are negative or could read that
way. None may appear in the draft until it has a verdict.

| ID | Claim as it stands | Current evidence | What the check must settle | Draft-safe wording until then |
|---|---|---|---|---|
| **N1** | "3 of 12 tools do no work" | `01`, static | They do work: they *retrieve* context that was pushed out. Are they only present when their feature is on? Our framing, not a fact | "Three of the twelve exist to manage the context window rather than the task" |
| **N2** | "`totalTokens` excludes cache tokens and misleads" | Observed in results | Source: how is it computed? Anthropic's own `input_tokens` leaves out cache reads and writes, so this may be faithful mirroring of the provider rather than a defect | "For cost, add the cache fields; `totalTokens` alone understates billed input" |
| **N3** | "Code mode is abandoned in ~8% of runs, at ~17× cost" | n=27 (24 instrumented) | Re-derive from the raw results with one definition. Confirm the task gave exact paths, since the path friction in N7b could itself cause fallbacks | "About one run in twelve on our task" |
| **N4** | "Code mode costs ~3× more on small data" | Small-data arm is **n=7** | Raise to n≥12. Median only; ranges overlap (25,625–50,353 vs 12,239–30,900) | "On small inputs the overhead can outweigh the saving" |
| **N5** | "Deprecated `structured_output()` invents data" | `20`: 3/3 invented, 0/6 | (a) Is it actually deprecated? (b) Source: does it run tools, or only structure the existing conversation? (c) **Fairness control:** call it *after* the agent has read the data in an earlier turn. (d) Does the docstring say so? | Hold. Likely "it structures the conversation so far; it doesn't fetch anything" |
| **N6** | "`shell`, `write`, `edit` on by default; interventions off" | Observed in `01` | Confirm in the source at the current version. Check whether docs warn, or ship a safer preset | "The defaults are built for a developer workstation" |
| **N7a** | "`read` returns `cat -n` numbered lines" | Observed | Intended and documented? (Claude Code's `read` does the same) | Likely a tip, not a flaw, or dropped |
| **N7b** | "`read` needs absolute paths and cannot list a directory" | One early run: 14 guesses | Retest relative paths and a directory path, with a control; read the docstring | Hold |
| **N7c** | "`agent.interventions` reports `[]` with Cedar active" | Observed | Where does the Cedar handler register? What is that attribute meant to hold? | Hold; probably drop |
| **N7d** | "`web_search` is off without native search" | Logged warning | By design and logged, so mention neutrally if at all | "Only available on models with native search" |
| **N8** | "Turning reasoning on made accuracy worse" | n=3 per cell: 3.0→1.7, 4.0→3.7 | Too small to claim "worse". Either raise n or soften | "Turning reasoning on did not close the gap" |

### Gaps to close before drafting

| ID | Gap | How to close it | Model calls? |
|---|---|---|---|
| **G1** | Observability and tracing: an intro would normally cover it, and we haven't looked | Find what the SDK exposes (metrics, hooks, OpenTelemetry). Run once with a console exporter and confirm spans for the model call and tool calls | Yes, a few |
| **G2** | Provider portability | Read which providers the model string resolves to. Early runs were on Bedrock (`FINDINGS.md` §1, §8). **Claim only what we ran;** no new credentials | No |
| **G3** | Version currency | Check PyPI and npm for releases after `strands-harness` 0.1.1 and `@strands-agents/harness` 0.1.0. A newer release means repeating the N-checks on it | No |
| **G4** | TypeScript package | State that it exists and its version. **No parity claim;** we haven't tested it | No |
| **G5** | Summarization's ~70% default | Quote it as configured in source, not observed. The mechanism itself is verified (`22`) | No |

### Out of scope for article 1

The detail goes to the follow-ups. Article 1 keeps one sentence each:
- The effort/reasoning confound and the cost crossover → article 2
- Variance, the 3.1M-token run, plain `Agent` vs harness nodes → article 3
- The full structured-output trap, MCP config detail, the production checklist → article 4

### Definition of done

1. Every register entry N1–N8 has a verdict and final wording.
2. G1–G5 are closed.
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

**Missing:** colliding tool names across servers, `mcp_router`, `tool_filters`, OAuth
MCP, and skills with bundled scripts.

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
