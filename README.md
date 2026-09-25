# Strands Harness: measured experiments and articles

This repository contains synthetic data, runnable experiments, raw JSON results,
and articles about [Strands Harness](https://github.com/strands-agents/harness-sdk).
Start with [AGENTS.md](AGENTS.md) for conventions and safe usage.

The agreed editorial direction is in [ARTICLE-PLAN.md](ARTICLE-PLAN.md): a practical
introduction, followed by a separate code-mode experiment. The complete revised
first draft is [ARTICLE-1.md](ARTICLE-1.md), with its evidence review in
[ARTICLE-1-REVIEW.md](ARTICLE-1-REVIEW.md). [FINDINGS.md](FINDINGS.md) is the detailed
experiment log. The older [ARTICLE-SERIES.md](ARTICLE-SERIES.md) is kept as a record
of earlier editorial decisions and its negative-claim checking rule.

## What the experiments cover

The scripts under `poc/` test tool orchestration, context management, memory,
sessions, skills, delegation, policy enforcement, MCP integration, and structured
output. Most agent runs used Claude Haiku 4.5 through the Anthropic API with
`effort="off"`. Original experiments used `strands-harness` 0.1.1; selected checks
were repeated on 0.1.2. Each numbered script writes a `results_*.json` file or names
the result it produced. Some original exploratory result files have no single
generating script, so trace each claim through the findings and its actual output.

The tool-orchestration benchmark compares `read` with `read` plus
`programmatic_tool_caller` on each of two datasets. The datasets were generated
independently. Within a dataset, both arms receive the same files and task.
Earlier summaries reported exact-figure accuracy tallies, but parts of the saved
answers are truncated and some graders match numeric substrings. Those exact
tallies are withheld from the revised first article pending the audit described in
[ARTICLE-1-REVIEW.md](ARTICLE-1-REVIEW.md). The code-mode behavior and raw usage
rows remain available for inspection.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "strands-harness[anthropic]" "strands-agents[cedar]"
cp .env.example .env        # add ANTHROPIC_API_KEY
.venv/bin/python poc/gen_data.py
.venv/bin/python poc/gen_data_large.py
cd poc && ../.venv/bin/python 01_inspect.py
```

`01_inspect.py` builds an agent but makes no model call. Most other numbered scripts
make paid calls, and repeated or multi-agent experiments can run many trials. The
older 0.1.1 environment and the separate 0.1.2 environment are described in
[AGENTS.md](AGENTS.md); pin versions when reproducing a number.

The example data under `data/vault/` is a decoy. Do not run an agent with privileged
cloud credentials: the default harness includes host shell and file tools, and tool
calls are not gated unless an intervention policy is configured. See the measured
path policy in [poc/03_interventions.py](poc/03_interventions.py) and the stronger
custom-tool execution counter in [poc/17_custom_tools.py](poc/17_custom_tools.py).
