# Article series plan

Where each piece stands, what evidence backs it, and what is still missing.

**Last updated:** 2026-09-22 · Start with [AGENTS.md](AGENTS.md). Evidence lives in
`FINDINGS.md`, `FINDINGS-MULTIAGENT.md`, `FINDINGS-EXTENDING.md`.

---

## The through-line

Each article makes one argument and proves it. The series argument is that **the
interesting engineering in agents has moved from the model to the scaffolding** — and
that most of the received wisdom about that scaffolding does not survive measurement.

Every piece so far has produced a result that contradicts the obvious expectation. That
is what makes them worth publishing rather than summarising a README.

---

## Article 1 — *Strands Harness: The Hard Part of AI Agents Was Never the AI*

**Status: drafted, needs one correction before publishing.**

**Thesis:** a quarter of the default toolset does no work; it fights the context window.
The library is a context-and-authority manager that happens to call a model.

**Evidence:** 12 tools with 3 doing no work · accuracy 4/20 vs 18/19 · the effort
control · offloading 9,928 vs 175,317 chars · subagent isolation 0 vs 2,400 markers ·
sandbox sealed · Cedar holds inside the sandbox.

**Correction — APPLIED 2026-09-22** (detail in `FINDINGS.md` §4): the draft says the model abandons
the sandbox *"roughly a quarter of the time"* and that the fallback run produced *"the
single wrong answer"*. With n=27 the real rate is **8%** (2/24 instrumented), or 19% if
counting every run over 100k. And of two fallback runs, one was 0/6 and one 6/6 — so
falling back is reliably **expensive** (~17×), not reliably **wrong**.

**Optional additions now that evidence exists:** `web_fetch` at 791× compression is a
vivid one-liner for the desk section; one sentence noting `Graph`/`Swarm` live in the
SDK, to close the "can it do multi-agent?" gap and set up article 2.

---

## Article 2 — the multi-agent piece

**Status: evidence gathered, not drafted.**

**Working title:** *Your Multi-Agent System Is Probably Just Expensive*

**Thesis:** the cost of a topology is not the story — the variance is. A `Graph` is no
dearer than one agent on small sequential work (0.92×) and 4.88× on bulky fan-out, but
its spread between best and worst run stays tight (2.2×, 6.6×) where a single agent's
reaches 119×. Structure buys predictability, not speed or accuracy.

**The unifying finding:** cost variance comes from the model choosing how to move data.
The single agent's 3.1M-token run had abandoned the code sandbox and read 42 files
directly — the identical failure article 1 documents. Structure helps because narrow
nodes leave fewer chances to take that path.

**Evidence:**
- Four architectures, same task: single 30,034 tokens / 23.4s; graph 2.0×; swarm 4.1×;
  subagent 4.9×. All four equally correct.
- The topology's *best case* (three independent analyses a graph can parallelise): the
  graph still lost — 59.2s vs 35.5s, 512,383 tokens vs 293,309.
- Why: each node is an independent agent with an empty context, so all three branches
  re-read the same 210KB. Fan-out triplicates the expensive part. Per-node timings prove
  parallelism happened (branches sum to 81.9s, wall was 59.2s) and still did not help.
- The one genuine win: isolation — 0 markers leaked vs 2,400.
- Delegation is safe: policy is inherited, and a child cannot exceed the parent's tools.

**Now verified:** conditional edges route correctly both ways, nested graphs work, and
`as_tool()`/`make_subagent()` behave as documented. Also: a harness agent makes a poor
narrow node — asked to classify in one word it wrote 149 words of troubleshooting, where
a plain `Agent` replied `URGENT`.

**Strongest missing experiment:** heterogeneous models per node — cheap model for
extraction, expensive one for synthesis. That is the best theoretical case for a graph
and it is untested. **Needs approval to use a non-Haiku model.**

**Also missing:** a task that genuinely does not fit one context window; cycles and
feedback loops; A2A.

---

## Article 3 — the practical build

**Status: evidence gathered, not drafted.**

**Working title:** *Everything You Plug Into This Agent Gets Treated the Same*

**Thesis:** custom tools, MCP servers and skills are first-class. Your tool is callable
from inside the code sandbox and governed by the same policy engine as `shell`. There is
no second-class tier and no hole where your code escapes authorization.

**Evidence:**
- A `@tool` function: registered, called, reachable inside the sandbox as an `async`
  function, and blocked by Cedar — with a counter proving it never executed.
- MCP: 14 tools from one server, namespaced, used without prompting. A broken server
  alongside it was isolated; the agent still built with all 14 working tools.
- Skills: an invented house format followed only when the folder was present.
- `web_fetch`: 1.4MB page → 1,800 chars, answer correct, no boilerplate.
- Intervention modes: `"smart"` and a plain-English policy both allowed a harmless call
  and blocked a money transfer; the control ran both.

**The sharpest hook:** the structured-output trap. The deprecated
`agent.structured_output()` does not run the agent loop — 3/3 runs invented service
names and scored 0/6, while every object validated cleanly. The supported
`structured_output_model=` route got 6/6. *A validated object is not a correct one.*

**Now verified:** MCP over streamable HTTP (auto-detected and explicit transport, with
headers); sessions across a real process restart.

**Missing:** multiple servers colliding on a tool name; `mcp_router`; a skill with
executable bundled scripts; `tool_filters`; OAuth-authenticated MCP.

---

## Possible article 4 — the frontier-model check

**Status: optional, pending approval. Not a blocker for articles 1-3.**

Every number in this series is Claude Haiku 4.5. The accuracy finding — a model getting
4/20 on arithmetic over data in its context — is the series' most striking claim and the
one most likely to be model-specific.

Three outcomes, all publishable:
1. **Opus fails too** → much bigger story than one library: frontier models cannot be
   trusted to compute over their own context, and code execution is not an optimisation
   but a correctness requirement.
2. **Opus succeeds** → article 1 needs qualifying to "on a small model", and the piece
   becomes about when cheap models need scaffolding that expensive ones do not.
3. **Partial** → the most useful engineering answer: where the boundary sits.

Standing constraint: the user asked for Haiku only. This stays queued as a *pending,
optional* item — articles 1-3 stand on their own without it, provided each states the
Haiku caveat plainly, which article 1 now does.

---

## Publication order and sequencing

1 → 3 → 2 → 4 is worth considering over strict numbering. Article 3 is the most
practical and highest-search-traffic, so it builds audience while article 2's remaining
experiments get done. Article 2 is the strongest contrarian argument and benefits from
readers already trusting the method.

Each stands alone. None depends on having read the others.
