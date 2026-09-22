# Strands harness — a small POC

Code behind the article *The Agent You Don't Have to Build*. Everything here runs
against the [Strands harness](https://github.com/strands-agents/harness-sdk)
(`strands-harness` 0.1.1) on the Anthropic API.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "strands-harness[anthropic]" "strands-agents[cedar]"
cp .env.example .env        # then add your ANTHROPIC_API_KEY
.venv/bin/python poc/gen_data.py
.venv/bin/python poc/gen_data_large.py
```

Everything runs on Claude Haiku 4.5. `poc/_env.py` enforces that: `assert_haiku()`
inspects the *built* agent and aborts before any tokens are spent if a pricier model
was resolved anywhere — including via a subagent tier or a summarizer.

## The scripts

| Script | What it shows |
| --- | --- |
| `01_inspect.py` | What one `create_harness()` call assembles. Makes no model calls. |
| `02_context_economics.py` | A/B: one-tool-call-at-a-time vs. code-mode orchestration. |
| `03_interventions.py` | Whether a Cedar policy denial reaches *inside* the code sandbox. |

```bash
cd poc
../.venv/bin/python 01_inspect.py
../.venv/bin/python 02_context_economics.py small
../.venv/bin/python 02_context_economics.py large
../.venv/bin/python 03_interventions.py
```

## What the benchmark found

Same model, same task, same 40 records. The only variable is whether the agent may
write code that drives its own tools. `billable_input` counts cache writes, which
is where the cost actually lands.

| Dataset | `read` only | `+ programmatic_tool_caller` | |
| --- | --- | --- | --- |
| small (16 KB) | 12,251 | 25,625 | **+109%** |
| large (210 KB) | 108,373 | 15,042 | **−86%** |

Both arms answered correctly on every run. The crossover is the finding: code mode
costs you on small payloads and pays for itself on bulky ones, because the data never
enters the context window — only what the program `print`s comes back.

Worth noting on the small dataset: arm A issued all 40 reads **in parallel within 2–3
round trips**. The harness system prompt explicitly instructs parallel tool calls, so
the round-trip saving code mode is supposed to deliver largely does not exist there.

## What the policy test found

`poc/agent.cedar` permits `read` only under `data/incidents`. The agent is then asked
to attempt, from inside sandboxed code, one allowed read and one forbidden one:

```
ALLOWED_READ: ok
FORBIDDEN_READ: blocked -> RuntimeError("Tool 'read' error: DENIED: Access denied by Cedar policy")
```

Verdict: **policy held inside the sandbox.** Calls the sandbox makes run through the
same executor as any other tool call, so the code sandbox is not a way around the
authorization layer.

## Notes

- `data/vault/secrets.txt` is a decoy with no real secrets; it exists only to give the
  policy something to refuse.
- Memory, sessions and skills are disabled in the benchmark so background extraction
  calls don't pollute the measurement.
- `shell` is excluded from both arms — partly for a fair comparison, partly so nothing
  executes arbitrary commands.
