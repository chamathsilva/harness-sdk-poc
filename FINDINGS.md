# Findings log — Strands Harness evaluation

Working record of every measurement taken, how it was taken, what it supports, and
what still needs doing. Written so a later session (or a follow-up article) can pick
up without re-deriving anything.

**Last updated:** 2026-09-22

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

**Three of twelve do no work** — `retrieve_context`, `retrieve_offloaded_content`,
`search_memory` exist only to recover context that was pushed out. This is the
article's central image and it is directly observable.

Also returned: `ContextManager`, `MemoryManager`, a session id, cache config
(`strategy='auto'`, system prompt + tools TTL on), and a 1,665-char system prompt
identical to `HARNESS_CONTRACT`.

Default model config observed: `global.anthropic.claude-opus-5`, `thinking: adaptive`,
`effort: high`, `max_tokens: 128000`, `context_window_limit: 1000000`.

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

Reasoning made it slightly *worse*, not better. The gap is not an artifact of the
effort setting.

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

> **CORRECTION REQUIRED IN ARTICLE 1.** The published draft says the model "simply does
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

## 6. Usability friction (observed, reproducible)

1. **`read` returns `cat -n` numbered lines.** Sandbox code parsing them as JSON fails
   on first attempt, every run. Agent recovers, costs a round trip.
2. **`read` needs absolute paths and cannot list a directory.** First attempt at the
   benchmark said "./data/incidents"; the agent made 14 increasingly desperate
   directory guesses before giving up. Tasks must state exact paths or provide `shell`.
3. **`agent.interventions` reports `[]`** even when a Cedar handler is active — the
   handler is not visible on that attribute. Minor observability wart.
4. **`web_search` is off** on models without native search, with a logged warning.

---

## 7. Claim → evidence matrix (for article fact-checking)

| Article claim | Evidence | Status |
|---|---|---|
| 12 tools, 3 do no work | `01` | Verified |
| Model bad at in-context arithmetic; program exact | `04`, `05` | Verified, n=39 |
| Crossover: code mode worse small, better large | `04` + extras | Verified, medians |
| Code mode sometimes catastrophically expensive | diagnostic | Verified, 3/12 |
| Sandbox has no file/network/process access | `06` | Verified w/ control |
| Cedar denial reaches inside sandbox | `03` | Verified |
| Subagent keeps work off parent's desk | `07` | Verified |
| Memory survives into new conversation | `08` | Verified |
| Skills auto-discovered from folder | `09` | Verified w/ control |
| Offloading swaps bulk for reference | `10` | Verified |
| Summarizes at ~70% utilization | `presets.py` source | **Read, not observed** |
| Delegate cannot be granted more perms than parent | `12` | Verified |
| Subagent inherits parent's Cedar policy | `11` | Verified |
| `web_fetch` distils rather than pastes | `13` | Verified, 791× |
| MCP servers discovered, namespaced, isolated on failure | `16` | Verified |
| Custom tools reach into the sandbox | `17` | Verified |
| Cedar governs custom tools, not just built-ins | `17` | Verified |
| `"smart"` and prose policies gate correctly | `19` | Verified w/ control |
| Structured output via `structured_output_model=` | `20` | Verified, 6/6 |
| Multi-agent topologies cost 2–5× a single agent | `14`, `15` | Verified, n=2 |

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

1. **Re-run the accuracy benchmark on Opus 5 / Sonnet 5.** Everything above is Haiku
   4.5. If a frontier model scores 18/20 on in-context arithmetic, the headline claim
   needs heavy qualification ("on a small model…") rather than being stated generally.
   **This is the single biggest open risk in the article.**
3. **Raise n on small-dataset code mode** (currently n=7).

### Priority 2 — remaining doc-sourced claims

7. **Context summarization at ~70%** — drive a conversation past the threshold and
   observe summarization happening, rather than trusting `presets.py`.

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
