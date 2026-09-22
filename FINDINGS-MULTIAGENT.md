# Findings — multi-agent patterns (material for article 2)

Evidence for a second article on `Graph`, `Swarm` and the harness's built-in
`subagent`. Same method as the first: measure, control, report what actually happened.

**Last updated:** 2026-09-22 · Start with [AGENTS.md](AGENTS.md). · All runs Claude Haiku 4.5, `effort="off"`, Anthropic API.

---

## Headline

**The cost of a topology is not the story. The variance is.**

At n=5, a `Graph` is no more expensive than a single agent (0.92× median) and is the
most *predictable* thing you can build — a 2.2× spread between its best and worst run,
against 4.4× for a single agent. Letting the model decide when to delegate is the
opposite: `subagent` costs 2.78× the median and swings **18.6×** between runs.

Structure does not buy speed or accuracy. It buys predictability. Handing control-flow
decisions to the model is what creates cost variance — the same pattern article 1 found
when the model chose whether to use the code sandbox.

The fan-out experiment makes the trade explicit: a single agent was 4.88× cheaper on the
median and then produced one run of **3.1 million tokens**, a 119× spread, while the
graph stayed inside 6.6×. Cheaper on average, or bounded at the worst — pick one.

> **This reverses an earlier conclusion.** At n=2 the medians read "topologies cost
> 2–5× a single agent". Five runs per arm dissolved that: the single-agent arm alone
> swings 29,575–130,212. Two runs per arm was an anecdote, exactly the mistake article 1
> made before repetition overturned it. Any claim in this file at n=2 should be treated
> as provisional.

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

### Complex task (n=5 per arch)

| arch | median billable | mean | min | max | spread | wall sec |
|---|---|---|---|---|---|---|
| single | 75,259 | 82,558 | 29,575 | 130,212 | 4.4× | 30.8 |
| **graph** | **69,572** | 63,358 | 37,781 | 82,003 | **2.2×** | 39.3 |
| swarm | 85,881 | 83,851 | 32,967 | 133,516 | 4.0× | 38.0 |
| **subagent** | **209,270** | 229,693 | 35,041 | **651,935** | **18.6×** | 53.3 |

Against the single agent's median: graph **0.92×**, swarm **1.14×**, subagent **2.78×**.

**All four were correct in all five runs** — 6/6 figures, 5/5 on naming the worst service.

Per-run values, sorted, showing how little the medians tell you:

```
single    29,575   48,839   75,259  128,906  130,212
graph     37,781   52,862   69,572   74,572   82,003
swarm     32,967   71,627   85,881   95,265  133,516
subagent  35,041   41,268  209,270  210,949  651,935
```

The graph's range is narrow and its worst case is better than the single agent's
median. The subagent's worst case is 18× its own best.

### Trivial task ("what is 17 × 23", n=5)

| arch | billable input | wall sec |
|---|---|---|
| single | 3,483 | 1.3 |
| graph | 5,745 | 2.9 |
| swarm | 4,101 | 1.5 |
| subagent | 4,361 | 1.4 |

All 5/5 correct everywhere. Overhead is modest in absolute tokens, but the graph took
2.2× the wall time for a one-line answer.

---

## Experiment 15 — the topology's best case: genuine parallelism

`poc/15_multiagent_parallel.py`. Three **independent** analyses over the bulky
(210 KB) dataset — by service, by root cause, by severity — then a synthesis.
A graph can run the three branches concurrently; a single agent cannot.

Graph shape: `splitter → [by_service, by_cause, by_severity] → synthesis`.

| arch | median billable | min | max | spread | wall sec | accuracy |
|---|---|---|---|---|---|---|
| single | **85,096** | 26,229 | **3,122,738** | **119×** | 30.7 | 5.8/6 |
| graph | 415,530 | 136,001 | 901,733 | **6.6×** | 46.7 | **6.0/6** |

On the median the graph costs **4.88×** and takes 1.52× the wall time. But look at the
spread. One single-agent run consumed **3.1 million tokens** — thirty-six times its own
median. The graph's worst run was 901,733, under seven times its best.

```
single  26,229   46,559   85,096   290,223  3,122,738
graph  136,001  183,633  415,530   828,990    901,733
```

**The trade is median cost against tail risk.** One agent is far cheaper most of the
time and occasionally catastrophic. The graph is dearer but bounded — and was slightly
more accurate, since each branch had one job.

This is the same shape as experiment 14, where the graph's spread was 2.2× against the
single agent's 4.4×. Across both experiments the graph's median moved (0.92× on small
sequential data, 4.88× on bulky fan-out) while its **predictability held**.

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
share a source, the topology duplicates the expensive part, and the duplication tax
scales with how much data each node must acquire. That is why the graph is at parity on
experiment 14's small sequential task and 4.88× here.

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

## The 3.1M-token run: one cause behind both articles

The single-agent outlier was worth chasing, because it turns out not to be a
multi-agent finding at all. Per-run tool calls for experiment 15's single arm:

| billable input | direct `read` calls | sandbox calls | accuracy |
|---|---|---|---|
| 26,229 | 2 | 3 | 6/6 |
| 46,559 | 2 | 6 | 6/6 |
| 85,096 | 2 | 7 | 6/6 |
| 290,223 | **44** | 9 | 6/6 |
| **3,122,738** | **42** | 15 | **5/6** |

The correlation is exact. Runs that stayed in the sandbox made two direct reads and
cost under 100k. The two expensive runs made forty-plus, pulling every file into the
context window — and the worst was also the only inaccurate one.

**This is the same failure article 1 documents** (`FINDINGS.md` §4): the model abandons
`programmatic_tool_caller` and fetches data itself. There it appeared in 8% of runs and
cost about 17×. Here it appeared in 2 of 5 and cost up to 36× the median.

So both articles share one root cause:

> **Cost variance in this harness comes from the model deciding how to move data, not
> from the architecture around it.** A deterministic `Graph` is more predictable
> precisely because it takes some of that decision away.

That reframes the multi-agent result. The graph's tighter spread is not a property of
graphs in general — it is that giving each node one narrow job leaves the model fewer
opportunities to choose the expensive path.


---

## Caveats on this block

- **Both experiments are now n=5.** Raising 14 from n=2 reversed its conclusion;
  raising 15 confirmed its direction and revealed the 119× single-agent tail.
- Even at n=5 these are medians of a very noisy process, not confidence intervals. The
  3.1M-token outlier is a single observation and should be described as such.
- The cost multiples are task-shaped, not universal: 0.92× on small sequential work,
  4.88× on bulky fan-out. Quote the ratio with its task, never on its own.
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
6. **Swarm under contention** — more than one agent plausibly able to handle a step.
