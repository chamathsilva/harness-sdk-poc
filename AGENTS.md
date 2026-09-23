# Start here

Orientation for anyone — human or agent — picking this repository up cold.

## What this is

An evaluation of the [Strands Harness](https://github.com/strands-agents/harness-sdk),
an open-source agent library from AWS whose harness packages landed on **2026-09-21**.
The goal is a hands-on introductory article on the framework, followed by deep-dive
articles, all arguing from measurement rather than restating the README.

Everything here is **evidence and the code that produced it.** Nothing is aspirational:
if a document states a number, a script in `poc/` produced it and the raw output is
committed in `poc/results_*.json`.

## Which file to read

Read in this order. Each is self-contained; you do not need the articles to use them.

| File | Read it when you want |
|---|---|
| **`AGENTS.md`** (this file) | Orientation. Conventions. What is safe to run |
| **`ARTICLE-SERIES.md`** | The plan: flagship article + deep dives, the negative-claim rule, article 1's critical-claim register and definition of done |
| **`FINDINGS.md`** | The master measurement log — context economics, accuracy, security, environment, open items |
| **`FINDINGS-MULTIAGENT.md`** | `Graph`, `Swarm`, `subagent` — evidence for article 3 |
| **`FINDINGS-EXTENDING.md`** | Custom tools, MCP, skills, structured output, sessions — evidence for article 4 |
| **`README.md`** | Short public-facing summary and setup instructions |

**Looking for one specific thing?**

- *Is claim X actually tested?* → the claim-to-evidence matrix in `FINDINGS.md` §7.
- *What should I test next?* → `FINDINGS.md` §9, prioritized. Multi-agent gaps are at
  the end of `FINDINGS-MULTIAGENT.md`; extension gaps at the end of `FINDINGS-EXTENDING.md`.
- *Why is a number what it is?* → every finding names its script. Raw results sit beside
  it in `poc/results_*.json`.
- *What must not be trusted yet?* → anything the matrix marks **Read, not observed** or
  **Not tested**.

## How the findings documents are structured

Each follows the same shape, so you can skim:

1. **Headline** — the single claim the document supports.
2. **Numbered findings** — each names the script, the method, the control, the result.
3. **Caveats** — sample sizes, confounds checked, what the result does *not* show.
4. **Still to do** — prioritized gaps.

When a finding corrects something already written, it is flagged inline as
`CORRECTION REQUIRED` with replacement wording, so the fix cannot be silently lost.

## Conventions that matter

**Every number is Claude Haiku 4.5.** Via the Anthropic API, `effort="off"` unless a
test says otherwise. The user's standing instruction is **Haiku only — do not run Opus
or Sonnet without asking.** `poc/_env.py::assert_haiku()` enforces this: it inspects the
*built* agent, not the call site, so a pricier model reaching in via a subagent tier or
a summarizer aborts the run before any tokens are spent.

**Cost metric.** Use `billable_input = inputTokens + cacheReadInputTokens +
cacheWriteInputTokens`. The SDK's `totalTokens` leaves out cache tokens, so on its own
it makes arm A of the main benchmark look 9× cheaper than it is. *(Whether that's a
defect or faithful mirroring of the provider's `input_tokens` is register N2. For our
metric it doesn't matter.)*

**Controls are mandatory.** Two tests in this repo initially "passed" while being
completely invalid — a sandbox-escape test where every attempt failed because the
*calling code* was wrong, and a policy test whose regex stripped the underscores out of
its own markers. Both were caught by a control. If a result has no control, treat it as
unverified.

**No negative claim ships unchecked.** Before anything is called broken, missing,
misleading or a bug, it goes through the five-step check in `ARTICLE-SERIES.md`:
current release, fresh reproduction, source, docs, and a correct-usage control plus an
upstream issue search. The verdict limits the wording. Documented behaviour is
described as a gotcha, never as broken.

**Don't trust the model's account of what happened.** Where it matters, tests assert on
side effects — a module-level counter proving a destructive tool never executed, a
unique marker string counted in the parent's conversation — not on the agent's prose.

## Running things

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "strands-harness[anthropic]" "strands-agents[cedar]"
cp .env.example .env          # add ANTHROPIC_API_KEY
.venv/bin/python poc/gen_data.py
.venv/bin/python poc/gen_data_large.py
cd poc && ../.venv/bin/python 01_inspect.py
```

**Two environments.** `.venv/` holds the originally tested versions (`strands-harness`
0.1.1). `.venv-new/` holds the current ones (0.1.2 / SDK 1.57.0); every re-validation
from `FINDINGS.md` §11 on ran there. Create it the same way, pinning those versions.

Scripts are numbered in the order they were written. `01_inspect.py` makes **no model
calls**. Everything else does, so each costs real money — small amounts on Haiku, but
`04`, `18` and the multi-agent scripts run many trials and are the expensive ones.

**Safety.** Do not point these at privileged cloud credentials. An earlier version ran
on AWS Bedrock with an `AdministratorAccess` key on an account holding live
infrastructure; `create_harness()` enables `shell`, `write` and `edit` by default with
`interventions` off, and an agent with shell access can read `~/.aws/credentials` like
any other file. See `FINDINGS.md` §8. `.env` is gitignored — keep it that way.

**Gotcha when writing new tests:** the agent streams its reply to stdout, so a result
line printed there interleaves with it and cannot be parsed back. Write results to a
file (see `poc/21_session_restart.py`).

## The three findings that matter most

If you read nothing else:

1. **Accuracy, not cost, is the story.** Asking one tool call at a time got all six
   figures right in 4 of 20 runs; letting the agent write code got 18 of 19. Turning
   reasoning on did not close the gap, so it is not an artifact of the `effort` setting.
2. **Structure buys predictability, not speed or accuracy** (n=5). A `Graph` came in
   at 0.92× a single agent on small sequential work and 4.88× on bulky fan-out, but its
   best-to-worst spread stayed at 2.2–6.6×. For a single agent it reached 119×, and for
   `subagent` 18.6×. The worst outliers share article 2's cause: the model abandoning the
   code sandbox. *(An earlier "2–5×" at n=2 was disproven. Don't reuse it.)*
3. **A validated object is not a correct one.** The deprecated
   `agent.structured_output()` formats what the conversation already contains and runs no
   tools, as its docstring says. Called cold, every object validated with every figure
   invented (0/3). Called after the agent had done the work, it was perfect (3/3). It's
   misuse of a deprecated method, not a bug (`27`).

## Known open item

The frontier-model check is **pending and optional**, not blocking. Every measurement is
Haiku 4.5, so the accuracy finding may be model-specific. Running it needs the user's
approval first.
