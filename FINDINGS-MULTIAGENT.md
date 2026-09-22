# Findings — multi-agent patterns (material for article 2)

Evidence for a second article on `Graph`, `Swarm` and the harness's built-in
`subagent`. Same method as the first: measure, control, report what actually happened.

**Last updated:** 2026-09-22 · Start with [AGENTS.md](AGENTS.md). · All runs Claude Haiku 4.5, `effort="off"`, Anthropic API.

---

## Headline

**Multi-agent topologies in this SDK cost 1.75×–4.9× more than a single agent and are
usually slower, with no accuracy benefit on the tasks tested.** They are not a free
upgrade. They pay for themselves only in the narrow case where isolation is the point.

This is the opposite of how multi-agent frameworks are usually marketed, and it is the
spine of article 2.

---

## What the SDK actually offers

Three distinct mechanisms, often conflated:

| Mechanism | Where | Shape |
|---|---|---|
| `subagent` | harness built-in tool | Model decides when to delegate; child is a full harness agent |
| `Graph` | `strands.multiagent` | Deterministic DAG, dependency-ordered, supports cycles and nesting |
| `Swarm` | `strands.multiagent` | Self-organizing team, shared memory, autonomous handoff, no central control |
| A2A | `strands.multiagent.a2a` | Agent-to-agent protocol — **not yet tested** |

`create_harness()` returns a plain `strands.Agent`, so harness agents can be graph
nodes or swarm members. Verified working.

### API shapes (verified by smoke test)

```python
from strands.multiagent import GraphBuilder, Swarm

b = GraphBuilder()
b.add_node(agent, "node_id")          # the JOIN node must exist before edges point at it
b.add_edge("from_id", "to_id")        # optional condition= for conditional routing
b.set_entry_point("node_id")
b.set_max_node_executions(10)
graph = b.build()
result = graph("prompt")              # GraphResult

swarm = Swarm([a, b, c], entry_point=a, max_handoffs=6, max_iterations=6)
result = swarm("prompt")              # SwarmResult
```

`GraphResult`: `status`, `results` (per node), `execution_order`, `accumulated_usage`,
`execution_time`, `completed_nodes`, `failed_nodes`.
`SwarmResult`: `status`, `results`, `node_history`, `accumulated_usage`.

Swarm members need `name` and `description` — handoff targets are chosen by name.

---

## Experiment 14 — four architectures, sequential task

`poc/14_multiagent.py`. Same 3-stage task (total per service → worst service + root
cause → remediation advice) on the 40 small records. Every arm had `read` and
`programmatic_tool_caller`, so arithmetic was done by code in all of them and the
accuracy gap from experiment 04 is not being re-measured. n=2 per arm.

### Complex task

| arch | billable input | output | wall sec | correct |
|---|---|---|---|---|
| **single** | **30,034** | 2,942 | **23.4** | 6/6 figures, 2/2 worst |
| graph | 59,984 | 5,334 | 34.0 | 6/6, 2/2 |
| swarm | 123,437 | 7,795 | 70.5 | 6/6, 2/2 |
| subagent | 145,950 | 6,354 | 42.7 | 6/6, 2/2 |

**All four were equally correct. The single agent was cheapest and fastest.**
Graph 2.0×, swarm 4.1×, subagent 4.9× the cost of one agent.

### Trivial task ("what is 17 × 23")

| arch | billable input | wall sec |
|---|---|---|
| single | 3,486 | 1.4 |
| graph | 3,956 | 3.4 |
| swarm | 4,101 | 2.2 |
| subagent | 4,361 | 1.6 |

All correct. Overhead is modest in absolute tokens, but graph took 2.4× the wall time
for a one-line answer.

---

## Experiment 15 — the topology's best case: genuine parallelism

`poc/15_multiagent_parallel.py`. Three **independent** analyses over the bulky
(210 KB) dataset — by service, by root cause, by severity — then a synthesis.
A graph can run the three branches concurrently; a single agent cannot.

Graph shape: `splitter → [by_service, by_cause, by_severity] → synthesis`.

| arch | wall sec | billable input | output | accuracy |
|---|---|---|---|---|
| **single** | **35.5** | **293,309** | 5,519 | 6.0/6 |
| graph | 59.2 | 512,383 | 14,070 | 6.0/6 |

**The graph lost its own best case.** 1.7× slower, 1.75× the input tokens, 2.5× the
output.

### Why — the data-loading tax

Per-node wall times, trial 1:

```
splitter 11.5s | by_cause 10.6s | by_service 17.5s | by_severity 53.8s | synthesis 2.4s
```

Branch times sum to 81.9s but wall time was 59.2s, so **parallelism did occur**. It
just did not help, because:

1. **Each node is an independent agent with an empty context.** All three branches read
   the same 210 KB of files separately. The work is triplicated; the single agent reads
   once and reuses.
2. **A fan-out is only as fast as its slowest branch** — here 53.8s, which alone
   exceeded the single agent's entire 35.5s run.
3. **The join node pays again**, restating all three analyses into its own context.

**Implication:** fan-out is worth it when branches touch *different* data. When they
share a source, the topology duplicates the expensive part.

---

## What topologies are genuinely good for

Not speed, and not accuracy. The one verified win is **isolation** (experiment 07):

| | parent conversation | markers leaked into parent |
|---|---|---|
| Delegated to subagent | 22,925 chars | **0** |
| Did it itself | 255,269 chars | **2,400** |

So the rule that fits all the evidence so far: **delegate to keep bulk out of a
long-running parent's context, not to go faster or be more correct.** You are buying
context hygiene and paying 2–5× in tokens for it.

And the security properties hold up (experiments 11, 12):
- A Cedar policy on the parent binds the child.
- A child cannot be granted tools the parent lacks.

So delegation is safe. It is just not cheap.

---

## Experiment 24 — conditional edges, nested graphs, and which agent to use as a node

### The finding that matters: don't put a harness agent in a narrow node

This cost a run to learn and is the most practically useful thing in this document.

A harness agent carries `HARNESS_CONTRACT`, which tells it to *keep working until the
task is fully resolved*. That is right for an autonomous agent and wrong for a
deterministic pipeline step. Asked to classify an incident in one word, with an
identical prompt (`results_node_agent_choice.json`):

| node built with | urgent input | routine input |
|---|---|---|
| plain `strands.Agent` | **1 word** — `URGENT` | **1 word** — `ROUTINE` |
| `create_harness(...)` | **149 words**, beginning *"There are no background recovery tasks currently running..."* | 18 words |

The harness agent stopped classifying and started troubleshooting the outage. My first
conditional-edge test failed entirely because of this — both inputs took the same branch,
since the classifier never emitted the word the condition looked for.

**Rule: plain `Agent` for narrow deterministic nodes; harness agent only where you
actually want autonomy.** This also partly explains experiment 14's cost gap: harness
agents in every node means every node is inclined to elaborate.

### Conditional edges work

`add_edge(from, to, condition=callable)` where the callable receives `GraphState`.
Conditions read `state.results[node_id]`; `str()` of a `NodeResult` contains the node's
text.

Run twice with opposite inputs, so a graph that always takes one path cannot pass by luck:

| input | execution order |
|---|---|
| "payments database is down, customers cannot check out" | `classifier → pager` |
| "a button is two pixels off centre" | `classifier → ticket` |

Exactly one branch ran each time. The unchosen node genuinely did not execute.

### Nested graphs work

A `Graph` passed to `add_node()` of another `Graph` runs as a single node. Inner graph
`doubler → adder` nested inside `inner_maths → reporter`, given "5", produced 15 and
completed. Execution order of the outer graph: `['inner_maths', 'reporter']`.

---

## Experiment 23 — `Agent.as_tool()` and `make_subagent()`

Both described in the series, neither previously run.

**`Agent.as_tool()`** produces a tool named after the agent (`reviewer`), registered via
`agent.tool_registry.register_tool(...)`. The specialist runs from its own conversation:
a secret planted in the caller's history **never appeared** in the specialist's messages.

**`make_subagent()`** derives its model-facing parameters from how each axis is declared.
With `instructions=Fixed(None)` and `model=Inherit()`, the tool schema exposed only:

```
['task', 'agent_type', 'tools']
```

Both `instructions` and `model` were removed from the schema entirely — the axis
declarations genuinely shape the API the model sees, rather than just defaulting values.

---

## Caveats on this block

- **n=2 per arm.** Directionally consistent across two independent experiments, but
  these are not tight confidence intervals. Raise n before publishing specific multiples.
- **Haiku 4.5 only.** A frontier model might coordinate a swarm more efficiently, or
  might make the single-agent baseline even stronger. Unknown.
- **My task designs may still favour the single agent.** Both tasks fit comfortably in
  one context window. A task that genuinely cannot fit — or needs different *models* per
  node, not just different prompts — is the untested case where topology should win.
- Swarm handoff behaviour was only exercised with linear hand-offs. Contested or cyclic
  coordination is untested.

---

## Still to do for article 2

1. **A task that does not fit one context window.** The honest test of whether topology
   earns its cost. Design: an analysis over data far exceeding the window, where a
   single agent must offload and re-retrieve while a graph splits naturally.
2. **Heterogeneous models per node** — a cheap model for extraction, an expensive one
   for synthesis. This is the strongest theoretical case for a graph and is untested.
   Requires approval to use a non-Haiku model.
4. **A2A protocol** — completely untested.
5. **Cycles / feedback loops** — conditional edges are verified, cycles are not.
5. **Raise n to 5+** on experiments 14 and 15.
6. **Swarm under contention** — more than one agent plausibly able to handle a step.
