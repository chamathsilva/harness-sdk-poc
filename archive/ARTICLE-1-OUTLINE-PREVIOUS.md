# Article 1 — outline for review (checkpoint B)

**Working title:** *Strands Harness, Hands-On: What AWS's New Agent Harness Actually Does*
**Reader:** engineers deciding whether to look at it this week. They know what an agent is;
they don't know Strands.
**Length:** ~3,500 words (the current draft is ~3,600 and covers less).
**Evidence base:** every claim traces to `FINDINGS.md`, re-validated on `strands-harness`
0.1.2 / SDK 1.57.0 (§11 static, §12 live). Wording for critical claims is fixed by the
register in `ARTICLE-SERIES.md`.

**Status:** approved 2026-09-23 with all five recommendations (D1–D5), and **applied to the doc**.

Fact-check fixes made during the rewrite, beyond the outline:
- "the four options stack" → only a Cedar policy layers, with one of the other three (per the `create_harness` docstring)
- `totalTokens`: compare the total (138) with the input alone (12,510), not total with input
- `structured_output()`: the docstring says it answers from conversation history; the *source* shows it runs no tools
- The subtitle no longer repeats the opening line; the as-of date is updated
- Doc renamed *Strands Harness, Hands-On*

---

## Decisions I need from you

| # | Question | My recommendation |
|---|---|---|
| D1 | **Title** | Keep the working title. The old one, *The Hard Part of AI Agents Was Never the AI*, moves to article 2 |
| D2 | **Accuracy numbers.** There are two runs: 4/20 vs 18/19 on 0.1.1, and 4/12 vs 10/12 on 0.1.2 | Lead with **4/20 vs 18/19**, add one sentence: "re-run on the new release: 4/12 vs 10/12" |
| D3 | **"The prompt in the box"** section (the six quoted contract rules) | Keep, but cut it by half. It's the draft's most original section and every quote checks out verbatim |
| D4 | **Your opinion that shipping permissions off is "a mistake"** | Keep it as opinion, but add that upstream flags it bluntly (`NotASandboxLocalEnvironment`). That's fairer and still pointed |
| D5 | **The CLI.** Mention it existence-only, or smoke-test it with Haiku first? | Existence-only, with the syntax taken from its README. The draft's example `git diff \| strands -p "…"` is wrong (see below) |

---

## Section by section

Labels: **Keep** = reuse the draft paragraph as is. **Fix** = reuse with a correction.
**New** = not in the draft. **Cut** = removed, with the reason.

### 0. Opening (~200 words)

| | Content | Source |
|---|---|---|
| New | Released 2026-09-21 by the Strands team at AWS, Apache-2.0. It's positioned as "a general-purpose agent rather than a coding agent", in the same space as Claude Code and Codex | Launch post |
| New | The vendor claims 28% lower token cost across six benchmarks and 77% cheaper than Claude Code on Terminal Bench 2.1. **Stated as theirs, not reproduced** | Launch post (G8) |
| Fix | "I spent a day building against it, then ran every claim as an experiment…". Keep the voice. Replace "two places my assumptions were wrong" with what the piece covers: what it is, what's in the box, what holds up, what to change before shipping | Draft ¶ "I spent a day…" |
| Cut | Subtitle *"A quarter of the tools … do no work at all"*, and ¶ "Of the twelve tools … three do no work whatsoever" | **N1: wrong.** `search_memory` reads long-term memory |
| Cut | ¶ "Everyone building AI agents … the model is the hard part" | The thesis framing now belongs to article 2 |

### 1. What it is (~350 words)

| | Content | Source |
|---|---|---|
| Fix | "What a harness actually is": keep the loop description, the engine/harness horse image and "the loop is a weekend's work". Compress six paragraphs to three | Draft §"What a harness actually is" |
| New | **Naming:** *Strands harness* (`pip install strands-harness`) is built on the *Strands Harness SDK* (PyPI `strands-agents`, public since May 2025) | Launch post, PyPI (V12) |
| Fix | **The one-call snippet.** Show `create_harness(model="anthropic/…")`, and say that with no argument it defaults to Bedrock Opus 5, which needs AWS credentials | Draft §"Three lines"; `defaults.py` (V10) |
| Fix | The "That agent goes and looks…" paragraph: keep, but soften it into an illustration rather than a measured claim | Draft |
| New | **Providers:** seven provider prefixes in the source; I ran two (Anthropic for every number; Bedrock early on) | G2 |
| New | **TypeScript** (`@strands-agents/harness` 0.1.1, Node ≥22) and the **CLI** (`strands`, with `/export` to Python or TypeScript), existence only | G4, G6 |
| Fix | CLI snippet: keep `strands "summarize what this repo does"`. **Replace** `git diff \| strands -p "write a commit message"`: per the CLI README, piped input is only used when no prompt is given, so as written the diff is ignored | V1 |

### 2. What's in the box — the tour (~2,100 words total)

Each item follows the same pattern: what it does, then what I measured.

**2.1 The tools (~250)**

- **Fix** the table. It becomes all 12 registered tools, grouped: *hands* (`read`, `write`, `edit`, `shell`, `web_fetch`), *orchestration* (`programmatic_tool_caller`, `subagent`, `todo_write`, background tasks), *context and memory* (`retrieve_context`, `retrieve_offloaded_content`, `search_memory`). Plus native web search, which is on for Anthropic but doesn't appear in the tool list.
- **Fix** the "three that stopped me" paragraphs, using N1's approved wording: two tools fetch back content moved out of the context window, and one searches long-term memory. Each arrives with the feature that needs it.
- **Keep** "`read` … also images and PDFs": the source confirms it where the model supports media.

**2.2 Context management: the desk (~280)**

- **Keep, compressed**: the desk metaphor (six paragraphs down to three). It's the draft's best explanatory device.
- **Fix** the offloading paragraph: 9,928 vs 175,317 characters. Credit **the default context management**, not `retrieve_offloaded_content` specifically. Both tools were active, so our test can't say which did the work (V6).
- **Fix** "summarizes as it goes, around 70%": it's **above 85%**, plus truncation of tool results over ~1,500 tokens (G5). Measured: 14 messages became 4. Don't say "halved".
- **Fix** `web_fetch`: replace the unmeasured "10,000-word article → two sentences" with the measurement, a 1.4 MB page down to 1,800 characters (791×) with the answer correct (`13`).

**2.3 Code mode and its sandbox (~500)** — the centrepiece, but the depth goes to article 2

- **Keep**: the "asking vs writing a program" explanation and the code snippet.
- **Fix** the sandbox paragraph: keep the escape attempts (ModuleNotFoundError / NameError — "absent, not blocked"). **Add one sentence:** this sandbox (Monty) is for code mode only. `shell` and the file tools run in a separate execution environment, which by default is your machine (G7).
- **Keep**: 4/20 vs 18/19, plus the replication line (D2). Keep "confidently names the right worst service…".
- **Fix** "reasoning on made it slightly worse" → "turning reasoning on didn't close the gap" (N8).
- **Fix** the cost table. Small-data row: 12,244 vs 23,749, about **2×** (was 3×). Bulky row unchanged (106,664 vs 28,912). Label the releases in the method box.
- **Fix** the caution section with N3's approved wording: about one run in ten (4 of 36) abandoned code mode; on bulky data those runs cost ~17× the median; half still got every figure right. Keep the 519,657-token worst case.
- **Keep** the bold summary line "handing arithmetic to a program … makes it correct", with a one-line pointer to article 2.

**2.4 Delegation and multi-agent (~200)**

- **Keep** the subagent isolation test (0 vs 2,400 leaked markers), moved here from "The desk".
- **New**, one line each: `Agent.as_tool()`, `make_subagent()` presets, and the fact that a delegate inherits the parent's policy (`11`, `12`, `23`).
- **New** teaser: `Graph` and `Swarm` ship in the SDK. At n=5 the graph wasn't cheaper but was the most predictable, with its best-to-worst spread under ~7× where a single agent's reached 119×. Pointer to article 3.

**2.5 Memory, sessions, skills (~300)**

- **Keep**: the three kinds of memory; the codeword test (a 73-character line in a markdown file); the skills folder; the house-format test with a control; "everything lands as readable files you can edit".
- **Fix** sessions: say it **survives a real process restart** (`21`), not "a crash does not lose the work".
- **New** caveat, one line: memory extraction runs in the background on a small model, so a short run can end with its last turns unsaved (V3).
- **Fix** the skills tree: drop `scripts/collect_commits.py`. We never tested bundled scripts.

**2.6 Plugging your own things in (~250)** — all new

- A custom `@tool`: callable from inside code mode, and governed by the same Cedar policy as `shell`. The destructive call was blocked, and the counter proves it never ran (`17`).
- MCP: 14 tools from one stdio server, namespaced; a broken server alongside it was isolated; streamable HTTP works too (`16`, `25`).
- Structured output: `structured_output_model=` got 3/3. The deprecated route goes to §3.

**2.7 Safety controls: the leash (~250)**

- **Keep**: the four `interventions` options, the plain-English policy, Cedar as Amazon's policy language, the four-line Cedar policy (verified against our file), and "the question worth asking" with its sandbox-read test.
- **Fix** "documented in a code comment" → documented in the `create_harness` docstring ("a subagent child inherits the policy so a delegate cannot bypass it").
- **Trim** to fit the budget.

**2.8 Observability (~80)** — new

- Tracing is off until you set `OTEL_TRACES_EXPORTER`. Then every agent call, model call, tool call and delegation becomes a span: 0 spans unset, 16 set (G1).

**2.9 The prompt in the box (~150)** — see D3

- **Keep, halved**: `HARNESS_CONTRACT` (1,665 characters). Keep four of the six quotes, all verified verbatim on 0.1.2 (V2); "read that list as a catalogue of how agents annoy people"; and "they ship the behaviour, you bring the job".
- **Cut**: "Most teams treat theirs as a trade secret…" and "a competitor cannot copy…". Unevidenced generalizations.

### 3. What surprised me (~200) — new

- **`totalTokens` understates cached runs:** 138 reported against 12,510 actual. It's a known open issue (#3546), and the article gives the fix (N2).
- **The deprecated `structured_output()`:** called cold, it returned schema-valid objects with every figure invented (0/3). Called after the agent had done the work, 3/3. That's by design, and the lesson is that a validated object isn't a correct one (N5). Pointer to article 4.

### 4. Before you ship it (~200)

- **Fix** "The defaults are braver than you are" with N6's approved wording. Keep the credentials point and "give it a scoped key".
- **Fix** the `read` paragraphs, turning them into tips (N7a/b): it numbers lines so the model can cite `path:line`, and it takes absolute paths while listing is `shell`'s job. **Cut** "fourteen increasingly desperate guesses": we had removed `shell` ourselves.
- **Fix** "It is very new": update to 0.1.2 / 1.57.0. **Cut** "documentation is thin exactly where you need it". That's an unchecked negative; the docs site exists. Replace it with the verified positive: the source is unusually well commented, e.g. the default environment's docstring.
- **Keep** "Web search is conditional", updated: native where the provider has it, and Exa opt-in on any model since 0.1.2 (N7d).

### 5. Verdict (~250)

- **Keep** the four "If you are…" paragraphs, with versions updated. "The SDK has been public for over a year" is verified.
- **Fix** the closing "The part that stays with me":
  - **Cut** "three tools whose only job is retrieving…" (N1).
  - Soften the permissions opinion per D4.
  - **Cut** the "honest … from the first line of its README" line. The README opens "A batteries-included agent, built on the Strands Harness SDK", so the claim is a stretch (V8).
- **New**, one paragraph: name the pattern the measurements kept showing (reliability comes from taking discretion away from the model), and point to articles 2–4.

### 6. Method box (~100)

- **Fix**: versions (0.1.1 for the original runs, 0.1.2 for re-validation), Haiku 4.5 only, `effort="off"`, the total run count (computed at fact-check), both repo links, the frontier-model caveat, and a note that the vendor benchmarks weren't reproduced.

---

## Word budget

| § | Words |
|---|---|
| 0 Opening | 200 |
| 1 What it is | 350 |
| 2 Tour | 2,160 |
| 3 Surprises | 200 |
| 4 Before you ship | 200 |
| 5 Verdict | 250 |
| 6 Method | 100 |
| **Total** | **~3,460** |

## How much of the draft survives

By my rough estimate, about **60%** of the draft carries over: kept, or kept with a correction. The rest is cut or rewritten because it was wrong, unmeasured, or belongs in articles 2–4. The biggest single change is the draft's central image, "a quarter of the tools do no work". It was wrong, and it's gone.

## Pre-draft checks run for this outline (no model calls)

| ID | Draft claim | Result |
|---|---|---|
| V1 | `git diff \| strands -p "…"` | **Wrong** per the CLI README; `strands "…"` is fine |
| V2 | The six quoted contract lines | All verbatim on 0.1.2 (1,665 chars) |
| V3 | "A small cheap model" extracts memory | Confirmed; extraction runs in the background (caveat added) |
| V4 | `session={"id": …}` | Valid |
| V5 | Skills load name and description first | Confirmed (source docstring) |
| V6 | Offloading credited to `retrieve_offloaded_content` | **Can't tell which tool did it.** Credit context management |
| V8 | README "honest from the first line" | A stretch; cut |
| V9 | The four-line Cedar policy | Matches `poc/agent.cedar` |
| V10 | `create_harness()` with no model | Bedrock Opus 5, needs AWS credentials; say so |
| V12 | SDK "public for over a year" | First release 2025-05-14; true |
