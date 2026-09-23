# Findings log — Strands Harness evaluation

Working record of every measurement taken, how it was taken, what it supports, and
what still needs doing. Written so a later session (or a follow-up article) can pick
up without re-deriving anything.

**Last updated:** 2026-09-22 · New here? Start with [AGENTS.md](AGENTS.md).

---

## 1. Environment — read this before comparing any number

| | |
|---|---|
| `strands-harness` | 0.1.1 (PyPI) |
| `strands-agents` (SDK) | 1.56.0 |
| `pydantic-monty` (sandbox) | 0.0.23 |
| `@strands-agents/harness` | 0.1.0 (npm) |
| Model | `claude-haiku-4-5-20251001` via **Anthropic API** |
| Reasoning effort | `off` unless a test says otherwise |
| Harness merged upstream | 2026-09-21, commit `4095cf5a6` |
| **Re-validated on** | `strands-harness` 0.1.2 + `strands-agents` 1.57.0 (both released 2026-09-22), static checks only; see §11 |

**Every number below is Haiku 4.5.** No Bedrock, no AWS credentials involved — an
earlier version of this POC ran on Bedrock and was moved off it deliberately (see §8).

`poc/_env.py::assert_haiku()` inspects the *built* agent and aborts before any tokens
are spent if a non-Haiku model resolved anywhere, including via a subagent tier or
summarizer. It has been verified to trip correctly on Opus.

### Metric definition

`billable_input = inputTokens + cacheReadInputTokens + cacheWriteInputTokens`

Cache writes are billed, so excluding them flatters whichever arm happened to cache
more. `totalTokens` from the SDK **excludes** cache tokens and is misleading for cost
comparison — do not use it.

---

## 2. What one `create_harness()` call assembles

Source: `poc/01_inspect.py`. Makes no model calls.

Twelve tools: `edit`, `programmatic_tool_caller`, `read`, `retrieve_context`,
`retrieve_offloaded_content`, `search_memory`, `shell`, `strands_manage_background_task`,
`subagent`, `todo_write`, `web_fetch`, `write`.

**Two of the twelve fetch back content the harness moved out of the context window**
(`retrieve_context` from the context manager, `retrieve_offloaded_content` from the
offloader plugin), and **a third, `search_memory`, searches long-term memory.** Each is
registered only with the feature that needs it. *The earlier "three of twelve do no
work" was wrong: `search_memory` is how memory is read. See §11, N1.*

Also on by default but not visible in `tool_names`:
- **Native `web_search`** on Anthropic models, as a provider tool (`anthropic_tools`:
  `web_search_20260318`). So it is 12 registered tools plus native search.
- **The `todos` and `environment` plugins** (`DEFAULT_BUILTIN_PLUGINS`). `01_inspect.py`
  printed `PLUGINS: []` because `Agent` has no `plugins` attribute. That was an
  artifact of our inspection, not a fact.

Also returned: `ContextManager`, `MemoryManager`, a session id, cache config
(`strategy='auto'`, system prompt + tools TTL on), and a 1,665-char system prompt
identical to `HARNESS_CONTRACT`.

Default model config observed on 0.1.1: `global.anthropic.claude-opus-5`, `thinking: adaptive`,
`effort: high`, `max_tokens: 128000`, `context_window_limit: 1000000`. **0.1.2 changed the
default effort to `"auto"`** (#4473). Our runs set `effort="off"` explicitly, so no measured
number is affected.

---

## 3. HEADLINE FINDING — accuracy, not cost

Source: `poc/04_repeatability.py`, `poc/05_control_effort.py`, plus extra trials.
Task: total `downtime_minutes` per service across 40 JSON records, one verifiable answer.

### Exact-figure accuracy (all six services correct)

| Arm | Perfect runs |
|---|---|
| One call at a time (`read` only) | **4 / 20** |
| Code mode (`+ programmatic_tool_caller`) | **18 / 19** |

Per-run exact-figure counts, one-call-at-a-time:
- small: `[1, 6, 0, 6, 5, 2, 2, 2, 0, 3]`
- large: `[2, 2, 4, 6, 5, 1, 6, 4, 2, 5]`

**Failure is silent.** The agent names the correct worst-offending service while
getting individual totals wrong by 50–100. Trial 1 large said notifications=1259
(truth 1160), auth=681 (truth 723). It reads as a confident, well-formatted answer.

### The confound was checked and ruled out

`effort="off"` was my cost-saving choice and would plausibly penalise mental
arithmetic. Re-ran arm A with reasoning **on**:

| dataset | effort | exact figures (mean of 3) |
|---|---|---|
| small | off | 3.0 / 6 |
| small | high | **1.7 / 6** |
| large | off | 4.0 / 6 |
| large | high | **3.7 / 6** |

Reasoning did not help: the means went down, but at n=3 per cell that's too small to
claim "worse" (register N8). The gap is not an artifact of the effort setting.

---

## 4. Cost — the crossover (secondary finding)

Median `billable_input`:

| | 40 small records (16 KB) | Same 40, bulky (210 KB) |
|---|---|---|
| One call at a time | **12,370** (n=10) | **106,664** (n=10) |
| Code mode | 37,997 (n=7) | 28,912 (n=12) |
| Delta | code mode **~3× worse** | code mode **~3.7× better** |

Ranges: arm A small 12,239–30,900; arm A large 106,659–108,373; code mode small
25,625–50,353; code mode large **14,658–519,657**.

**Why the small-data penalty exists:** arm A issues all 40 reads *in parallel* within
2–3 round trips. `HARNESS_CONTRACT` explicitly instructs parallel tool calls, so the
round-trip saving code mode is supposed to deliver largely does not exist there.

### The fallback failure mode — corrected with a larger n

`poc/18_abandonment_rate.py` plus every earlier code-mode run. **n=27 large-dataset
code-mode runs, 24 of them instrumented** (tool calls recorded).

A run "fell back" when it made 10+ direct `read` calls instead of letting sandboxed
code do the fetching.

| | n | median billable input |
|---|---|---|
| Used the sandbox | 22/24 | **26,650** |
| Fell back to direct reads | **2/24 (8%)** | **469,484** (17.6× worse) |

Runs exceeding 100k billable input: **5/27 (19%)** — costs were 115,825 · 413,313 ·
419,311 · 458,865 · 519,657. Note 19% > 8%: one expensive run did *not* fall back, so
cost blow-ups have more than one cause.

The instrumented example remains the clearest illustration
(`results_codemode_diagnostic.json`):

| trial | direct `read` calls | sandbox calls | billable_in | exact |
|---|---|---|---|---|
| 1 | 1 | 5 | 36,546 | 6/6 |
| 2 | 0 | 5 | 31,052 | 6/6 |
| **3** | **40** | 5 | **519,657** | **0/6** |
| 4 | 1 | 4 | 25,940 | 6/6 |
| 5 | 1 | 4 | 22,468 | 6/6 |

> **CORRECTION — APPLIED TO ARTICLE 1 on 2026-09-22.** Kept here as the record. The published draft says the model "simply does
> not take the deal" *"roughly a quarter of the time"*, and that the fallback run
> produced "the single wrong answer". Both overstate it:
> - The measured fallback rate is **8%** (2/24), or **19%** if you count every run that
>   blew past 100k. "Roughly a quarter" came from n=12.
> - Of the two observed fallback runs, one scored 0/6 and the other **6/6**. Falling
>   back is reliably *expensive*, not reliably *wrong*.
>
> Suggested wording: "about one run in twelve abandoned the sandbox, and roughly one in
> five cost far more than it should have — when that happens you pay around 17× the
> normal cost, and the answer may or may not survive."

Overall code-mode accuracy across every graded large run: **22/23 perfect**.

**The same failure shows up in the multi-agent work.** Experiment 15's single-agent arm
produced a 3,122,738-token run — 36× its own median and the only inaccurate run in that
arm — and its tool calls show 42 direct reads against 2 in the cheap runs. See
`FINDINGS-MULTIAGENT.md`. Both articles share one root cause: **cost variance comes from
the model deciding how to move data**, not from the architecture around it.

---

## 5. Verified claims (each with a control)

### Sandbox is genuinely sealed — `poc/06_sandbox_boundary.py`

Nine escape attempts, all blocked. **A control statement (`print(sum(range(10)))` →
`45`) executed**, proving the test harness itself worked — the first version of this
test was invalid because my calling API was wrong and every attempt "failed" for the
wrong reason.

| Attempt | Mechanism |
|---|---|
| `open("/etc/hosts")` | PermissionError |
| `import os` | PermissionError |
| `subprocess`, `socket`, `urllib` | **ModuleNotFoundError** |
| `__import__("os")`, `__builtins__`, `__file__` | **NameError** |

The classic escape hatches are not guarded — they do not exist. Correct API for
driving a tool directly: `agent.tool.<tool_name>(**kwargs)`.

### Subagent isolation — `poc/07_subagent_isolation.py`

Each bulky record carries unique `trace_id=` values, used as a leak tracer.

| | parent conversation | distinct trace_ids in parent |
|---|---|---|
| Delegated to subagent | 22,925 chars | **0** |
| Did it itself | 255,269 chars | **2,400** |

### Memory persists — `poc/08_memory.py`

Taught agent #1 an unguessable fact, flushed, built a **separate** agent over the same
memory dir. Recalled both codeword and owning team. Stored as
`deploy-freeze-codeword-is-juniper-thicket-and-is-o.md`, 73 chars, human-readable.

### Skills discovered — `poc/09_skills.py`

Invented a house format no model would produce unprompted. Prompt never mentions the
skill. With skills on: format followed. With skills off (control): not followed.

### Offloading — `poc/10_offloading.py`

400KB file, read with offloading on vs off:

| | conversation | retrieval tool present |
|---|---|---|
| Offloading on (default) | **9,928 chars** | yes |
| Offloading off | 175,317 chars | no |

Note: `read` caps at 2,000 lines by default, so the file's tail was never reached in
either arm. The size difference reflects offloading of the 2,000-line result.

### Cedar policy holds inside the sandbox — `poc/03_interventions.py`

Policy permits `read` only under `data/incidents`. From inside sandboxed code:

```
ALLOWED_READ: ok
FORBIDDEN_READ: blocked -> RuntimeError("Tool 'read' error:
                DENIED: Access denied by Cedar policy")
```

Sandbox calls route through the same executor. Not an escape path.

---

## 5b. Summarization fires and compacts the history — `poc/22_summarization.py`

The last doc-sourced claim in article 1. Six turns, each planting a distinctive fact,
then a probe for the first one.

Filling Haiku's real 200k window to hit the default trigger (85% under `"auto"`; see §11, G5) would be costly, so the
test shrinks the window the context manager measures against (`AnthropicModel(...,
context_window_limit=2000)`) and fires at `utilization=0.5`.

| | messages after 6 turns | history chars | still answers turn 1 |
|---|---|---|---|
| Context management **on** | **4** | **2,011** | yes |
| Off (control) | 14 | 4,414 | yes |

**14 messages collapsed into 4, history halved, answer still correct.**

Two things worth recording:

1. **The facts survive summarization.** My first pass expected the early fact to vanish
   from history; it did not, because the summary carries it. A summary that dropped the
   facts would be a bad summary. The signal is message count and history size falling,
   not content disappearing.
2. **`threshold` and `utilization` are not interchangeable.** Conversation summarization
   triggers on `utilization` (a fraction of the context window). `threshold` (an absolute
   token count) is what the *tool-result* strategies use. Two runs at
   `threshold=1500` then `threshold=400` never fired before this was understood.

Caveat: this verifies the mechanism at a forced trigger point. The shipped default of
85% utilization (`context_manager="auto"`) on a real window is still unobserved.

---

## 6. Usability friction (observed, reproducible)

1. *(Verdict: documented design, tip only; §11 N7a.)* **`read` returns `cat -n` numbered lines.** Sandbox code parsing them as JSON fails
   on first attempt, every run. Agent recovers, costs a round trip.
2. *(Verdict: documented; our friction came from removing `shell`; §11 N7b.)* **`read` needs absolute paths and cannot list a directory.** First attempt at the
   benchmark said "./data/incidents"; the agent made 14 increasingly desperate
   directory guesses before giving up. Tasks must state exact paths or provide `shell`.
3. *(Verdict: OUR ARTIFACT. `Agent` has no such attribute; the handler is in `_intervention_registry`. Dropped; §11 N7c.)* ~~**`agent.interventions` reports `[]`**~~ even when a Cedar handler is active — the
   handler is not visible on that attribute. Minor observability wart.
4. *(Verdict: documented; on Anthropic it is native and on; `"exa"` works anywhere since 0.1.2; §11 N7d.)* **`web_search` is off** on models without native search, with a logged warning.

---

## 7. Claim → evidence matrix (for article fact-checking)

| Article claim | Evidence | Status |
|---|---|---|
| 12 tools, 3 do no work | `01` | Verified |
| Model bad at in-context arithmetic; program exact | `04`, `05` | Verified, n=39 |
| Crossover: code mode worse small, better large | `04` + extras | Verified, medians |
| Code mode sometimes catastrophically expensive | `18` + diagnostic | Verified, n=27: 2/24 fell back, 5/27 over 100k |
| Sandbox has no file/network/process access | `06` | Verified w/ control |
| Cedar denial reaches inside sandbox | `03` | Verified |
| Subagent keeps work off parent's desk | `07` | Verified |
| Memory survives into new conversation | `08` | Verified |
| Skills auto-discovered from folder | `09` | Verified w/ control |
| Offloading swaps bulk for reference | `10` | Verified |
| Summarization compacts history | `22` | Mechanism verified at forced trigger |
| ~~The ~70% default~~ **Default `"auto"` summarizes at 85%**, truncates tool results over 1,500 tokens | `context_manager.py` source + launch post | **Read, not observed** (70% was a misread; it belongs to a non-default preset) |
| Delegate cannot be granted more perms than parent | `12` | Verified |
| Sessions survive a process restart | `21` | Verified, 2 processes |
| Subagent inherits parent's Cedar policy | `11` | Verified |
| `web_fetch` distils rather than pastes | `13` | Verified, 791× |
| MCP servers discovered, namespaced, isolated on failure | `16` | Verified |
| Custom tools reach into the sandbox | `17` | Verified |
| Cedar governs custom tools, not just built-ins | `17` | Verified |
| `"smart"` and prose policies gate correctly | `19` | Verified w/ control |
| Structured output via `structured_output_model=` | `20` | Verified, 6/6 |
| ~~Multi-agent topologies cost 2–5× a single agent~~ | `14`, `15` | **Disproven at n=5** |
| Graph is more predictable than a single agent or subagent | `14`, `15` | Verified, n=5 |
| Conditional edges, nested graphs, `as_tool()`, `make_subagent()` | `23`, `24` | Verified |
| MCP over streamable HTTP | `25` | Verified |

> **Negative or critical claims** ("does no work", the `totalTokens` gotcha, the
> structured-output trap, default tool exposure, the `read` friction) carry **no status
> here until they pass the five-step check.** Their live status is the critical-claim
> register in `ARTICLE-SERIES.md` (N1–N8).

---

## 8. Safety note carried forward

The first environment for this POC used AWS Bedrock via an IAM user with
**AdministratorAccess** and a static access key **1,546 days old**, on an account
running live infrastructure (~$4.9k/month: EC2, RDS, ElastiCache, Secrets Manager,
plus existing Bedrock spend). `create_harness()` enables `shell`, `write` and `edit`
by default with `interventions` off — an agent with shell access can read
`~/.aws/credentials` like any other file.

Moved to a scoped Anthropic API key. **Do not run agent POCs against privileged
credentials.** This is the basis for the article's warning in "Where it bites".

---

## 9. Must-do further evaluations

Ordered by how much they would change what we can claim.

### Priority 1 — the accuracy finding may be model-specific

> **Item 1 is OPTIONAL and pending the user's approval** (Haiku-only standing
> instruction). It is not a blocker: articles 1-3 stand provided each states the Haiku
> caveat, which article 1 now does.

1. **Re-run the accuracy benchmark on Opus 5 / Sonnet 5.** Everything above is Haiku
   4.5. If a frontier model scores 18/20 on in-context arithmetic, the headline claim
   needs heavy qualification ("on a small model…") rather than being stated generally.
   **This is the single biggest open risk in the article.**
3. **Raise n on small-dataset code mode** (currently n=7).

### Priority 2 — remaining doc-sourced claims


### Priority 3 — breadth for a follow-up piece

8. Cost in **dollars**, not tokens, across providers.
11. Session resume **across process restart**, not just across agent objects.
12. `context_manager="auto"` vs `"agentic"`.
13. TypeScript parity — is `createHarness()` equivalent?
14. Latency/wall-clock, which was noted but never treated as a measured result.
15. Structured output and multi-agent patterns.

---

## 10. Reproducing

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "strands-harness[anthropic]" "strands-agents[cedar]"
cp .env.example .env    # add ANTHROPIC_API_KEY
.venv/bin/python poc/gen_data.py
.venv/bin/python poc/gen_data_large.py
cd poc
../.venv/bin/python 01_inspect.py
../.venv/bin/python 04_repeatability.py 3
../.venv/bin/python 05_control_effort.py 3
../.venv/bin/python 06_sandbox_boundary.py
../.venv/bin/python 07_subagent_isolation.py
../.venv/bin/python 08_memory.py
../.venv/bin/python 09_skills.py
../.venv/bin/python 10_offloading.py
```

Raw results land in `poc/results_*.json` and are committed as evidence.

---

## 11. Phase 1 re-validation — static checks on the current release (2026-09-22)

The five-step rule in `ARTICLE-SERIES.md` applied to every critical claim article 1
could make, plus the gaps. **No model calls.** Checks were run against
`strands-harness` **0.1.2** and `strands-agents` **1.57.0**, both released on
2026-09-22, installed side by side in `.venv-new/` so old and new source could be
diffed.

### What changed upstream, and what it touches

| Change | PR | Touches |
|---|---|---|
| Default `effort` `"high"` → `"auto"` | #4473 | §2 default config. Our runs set `"off"`, so no numbers change |
| `web_search: "exa"` now wins over native search on any model | #4491 | N7d |
| New vended tools: `mcp_router`, `handoff_to_user` | #4252, #4348 | Article 4's "missing" list (`mcp_router` now exists) |
| MCP auth-flow and framing fix (82 lines in `tools/mcp/_compat.py`) | #4233 | `16`, `25`: re-run on 0.1.2 |
| Summaries keep only text when re-roled (38 lines in `context_compression.py`) | #4402 | `22`: re-run on 0.1.2 |
| Schema normalization no longer mutates caller specs | #4426 | `17`: re-run on 0.1.2 |
| Graph / Swarm / tool executor | — | Import-line changes only |
| Harness package itself | — | 4 files: the effort default and `web_search` precedence only. The default tool list is identical (12) |

Also released: TypeScript harness 0.1.1 and **`@strands-agents/cli` 0.1.1**. The CLI ships
the `strands` terminal command; it's untested (G6).

### Verdicts

| ID | Claim | Verdict | Deciding evidence |
|---|---|---|---|
| N1 | "3 of 12 tools do no work" | **Wrong: our framing.** Dropped | `memory/memory_manager.py:475`: `search_memory` searches long-term memory. `_context_manager/retrieval_tool.py:3`: `retrieve_context` is "registered automatically when the ContextManager has storage configured". `retrieve_offloaded_content` comes from the context-offloader plugin |
| N2 | "`totalTokens` excludes cache tokens" | **Confirmed defect, known upstream** | `models/anthropic.py:816`: `totalTokens = input_tokens + output_tokens`. Issue **#3546** (open since 2026-07-29) says Anthropic direct "under-reports a cached run", Bedrock includes cache, and OpenAI-style providers count it *inside* input. Our metric matches Anthropic's documented total |
| N3 | "Code mode abandoned ~8%, ~17× cost" | **Confirmed (model behaviour, not a framework defect)** | Re-derived from raw rows in 4 files: **2/24 = 8.3%**, medians 26,650 vs 469,484 (**17.6×**), exact scores 0/6 and 6/6. The prompt gave the absolute directory, the file range and "Use absolute paths", so path friction was not the cause |
| N4 | "Code mode ~3× dearer on small data" | **Pending phase 2** | n=7, and the ranges overlap |
| N5 | "Deprecated `structured_output()` invents data" | **Documented behaviour.** Fairness control still required | `agent/agent.py:962`: `DeprecationWarning` pointing to `structured_output_model`. The implementation is one `model.structured_output(...)` call over the existing messages, with no event loop and no tools. The docstring: "use only the existing conversation history to respond" |
| N6 | "`shell`/`write`/`edit` on; interventions off" | **Confirmed and documented, bluntly** | `defaults.py`: `DEFAULT_BUILTIN_TOOLS` covers all built-ins. `agent.py:388`: interventions "defaults to `None` (off — every call runs)". `agent/agent.py:352`: the default environment is `NotASandboxLocalEnvironment`, "runs … on the host with **no isolation**. The deliberately blunt name … is a warning". Docker and SSH sandboxes exist |
| N7a | "`read` returns `cat -n` lines" | **Documented design.** Tip only | `tools/file_tools.py:74`: "numbered lines so you can cite `path:line`" |
| N7b | "`read` needs absolute paths, can't list dirs" | **Documented.** Tip only | `file_tools.py:25`. Reproduced deterministically with no model: `./x` and `x` are rejected with "should start with '/'", and `..` is rejected as traversal. Directory listing is `shell`'s job, and `shell` is on by default; our friction came from removing it |
| N7c | "`agent.interventions` reports `[]`" | **Our misuse.** Dropped | `Agent` has **no** `interventions` attribute; `getattr(..., [])` returned our own default. The registry holds `['CedarAuthorization']` when a policy is passed. Same artifact as `PLUGINS: []` |
| N7d | "`web_search` off without native search" | **Documented** | On Anthropic it's native and **on** (`anthropic_tools: web_search_20260318`). It's off only where the provider has no native search; `"exa"` serves any model since #4491 |
| N8 | "Reasoning made accuracy worse" | **Softened** to "did not close the gap" (n=3 per cell) | Raising n is optional in phase 2 |

### Gaps

| ID | Result |
|---|---|
| G1 observability | **Source read; run pending.** Per `strands_harness/telemetry.py`, the SDK already emits spans for the model loop, tool calls and subagent delegation. The harness wires an exporter only when `OTEL_TRACES_EXPORTER` is `otlp` or `console`; unset means off. Phase 2: one run with the console exporter |
| G2 providers | **Closed.** `models.py:296` resolves `bedrock`, `bedrock-mantle`, `anthropic`, `openai`, `google`, `ollama` and `litellm` prefixes, plus `Model` instances. We ran two: Anthropic (all numbers) and Bedrock (early, not kept). The article claims only those two |
| G3 version currency | **Closed**, as above |
| G4 TypeScript | **Closed.** `@strands-agents/harness` 0.1.1 is published and needs Node ≥22. Existence only; no parity claim |
| G5 summarization default | **Closed, and corrected.** The harness default `context_manager="auto"` summarizes at **85%** utilization and truncates tool results over **1,500** tokens to 750-token previews (`_context_manager/context_manager.py:31-34`). The **70%** we'd been quoting is the non-default `proactive_summarization` preset. The launch post confirms "~1500 tokens" and "above 85%". Source warns that preset values "may change between releases" |
| G6 Strands CLI | **New, untested.** `strands` command; `/export` produces Python or TypeScript. Existence only unless tested (its default model is Bedrock Opus 5, so it would need Haiku configured) |
| G7 execution sandboxes | **New, untested.** Docker and SSH environments exist in `strands/sandbox/`. **Article 1 must separate the two sandboxes:** Monty (code mode, sealed, verified by `06`) versus the execution environment for `shell`/files (host by default) |
| G8 vendor benchmarks | **New.** The launch post claims 28% lower token cost than Claude Code and Codex across six benchmarks, and 77% cheaper on Terminal Bench 2.1 with Fable 5. Cite as the vendor's claims; not reproduced |

### Naming, per the launch post

*Strands harness* (`pip install strands-harness`) is built on the *Strands Harness SDK*
(PyPI `strands-agents`), in the `strands-agents/harness-sdk` monorepo. It's
positioned as "a general-purpose agent rather than a coding agent".
