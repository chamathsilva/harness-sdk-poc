# Findings — extending the harness (material for article 3)

Evidence for a practical article on custom tools, MCP, and skills: *how you actually
build something on this thing.*

**Last updated:** 2026-09-22 · All runs Claude Haiku 4.5, `effort="off"`, Anthropic API.

---

## Headline

**Whatever you plug in gets treated exactly like a built-in.** A tool you write is
callable by the model, reachable from inside the code sandbox, and governed by the same
Cedar policy as `shell` or `read`. There is no second-class tier for your own code, and
no hole where your tools escape the authorization layer.

That uniformity is the story worth telling. Most frameworks leak somewhere.

---

## 1. Custom tools — `poc/17_custom_tools.py`

A tool is a decorated function. The docstring and type hints become the schema the
model sees:

```python
from strands import tool

@tool
def lookup_ticket(ticket_id: str) -> str:
    """Fetch a support ticket by its id.

    Args:
        ticket_id: The ticket identifier, e.g. TKT-42.
    """
    return json.dumps({"id": ticket_id, "status": "open", "owner": "raft-team"})

agent = create_harness(tools=[lookup_ticket])
```

Three things verified, each with a real check rather than taking the model's word:

| Question | Result | How it was checked |
|---|---|---|
| Registered and called? | **Yes** | Module-level counter incremented; answer contained `raft-team` |
| Reachable inside the sandbox? | **Yes** | `await lookup_ticket(ticket_id="TKT-99")` inside `programmatic_tool_caller` returned the record |
| Governed by Cedar? | **Yes** | A policy omitting `delete_everything` blocked it — the counter proves it **never executed**, not merely that the model reported an error |

The sandbox result matters for anyone building real orchestration: your own tools
become `async` functions the agent can loop over, filter and parallelise in code,
exactly like `read`.

The Cedar result matters more. Your tool name becomes a Cedar action automatically:

```
permit(principal, action == Action::"lookup_ticket", resource);
// delete_everything is simply never permitted, so it is denied.
```

Cedar is default-deny, so a destructive tool you forget to mention is off, not on.

### Other ways in

- `Agent.as_tool()` — wrap a whole agent as a callable tool, named after the agent.
- `make_subagent(builder=...)` — a configured delegation tool with fixed roles, model
  tiers and prompts, where each axis is `Fixed`, `Inherit`, `Open` or `Choice`.

---

## 2. MCP — `poc/16_mcp.py`

Point `mcp_servers` at a standard `mcpServers` config, as a file path or inline:

```python
create_harness(mcp_servers={
    "incidents": {"command": "npx",
                  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/data"]},
})
```

**Result: 14 tools discovered from one server and merged into the tool list**, all
namespaced with the server's key:

```
incidents_read_file          incidents_list_directory      incidents_search_files
incidents_read_text_file     incidents_directory_tree      incidents_write_file
incidents_read_multiple_files  incidents_get_file_info     incidents_move_file
incidents_edit_file          incidents_create_directory    incidents_read_media_file
incidents_list_directory_with_sizes   incidents_list_allowed_directories
```

The model used them without prompting about MCP at all — asked to list files, it called
`incidents_list_directory` and correctly reported 40.

### Failure isolation — verified

Config with one impossible server (`definitely-not-a-real-command`) alongside a good one:

```
error=<client initialization failed: No such file or directory:
'definitely-not-a-real-command'> | MCP server failed to start, continuing with no tools
```

The agent **still built**, and all 14 tools from the working server survived. A broken
server contributes nothing rather than taking the agent down. Set
`"continue_on_error": false` on a server to make its failure fatal instead.

### Namespacing detail

Characters outside `[A-Za-z0-9_-]` in a server name become `_`. Set `"prefix"` to choose
the namespace, or `"prefix": ""` to opt out. `"disabled": true` skips a server entirely.

**Practical note:** the first run pays an `npx` fetch. Budget for cold-start latency.

---

## 3. Skills — `poc/09_skills.py`

A skill is a folder with a `SKILL.md`: YAML frontmatter (`name`, `description`) then
markdown instructions. Drop it in `./.agent/skills` and it is found automatically.

```
.agent/skills/
└── incident-brief/
    ├── SKILL.md
    └── scripts/collect_commits.py     # optional bundled files
```

Verified causally: an invented house format ("begin with `INCIDENT BRIEF //`, end with
`FILED UNDER:`") was followed **only** when the folder was present, using a prompt that
never mentioned the skill. Control run without it did not follow the format.

Only name and description sit in context up front; full instructions load on demand via
a `skills` tool. So twenty skills do not crowd the context window.

Point elsewhere with `skills="path"`, a git URL, or a list of either.

---

## 4. Choosing the tool set

```python
create_harness(builtin_tools=["read"])                       # pin exactly these
create_harness(builtin_tools=[])                             # none; bring your own
create_harness(builtin_tools={"subagent": False})            # defaults minus one
create_harness(builtin_tools={"*": False, "read": True})     # start empty, add back
create_harness(builtin_tools={"web_fetch": {"model": "anthropic/claude-haiku-4-5-20251001"}})
```

A **list pins**; a **mapping edits**. Four tools take config: `shell` (`description`),
`web_fetch` (`model`, `transport`), `programmatic_tool_caller` (`allowed_tools`,
`timeout`), `subagent` (`max_depth`).

Gotcha: a list pins every name it contains, so naming `web_search` on a model without
native search **raises** rather than quietly staying off. Use the mapping form for
"defaults minus X".

### The wider SDK tool library

Beyond the harness built-ins, `strands.vended_tools` has `file_editor`, `http_request`,
`handoff_to_user`, `notebook`, `sleep`, `mcp_router`, `shell`. Pass them via `tools=`.

---

## 5. web_fetch — `poc/13_web_fetch.py`

Worth its own mention because the numbers are striking. A 1,424,120-byte Wikipedia page
produced an **1,800-character** conversation — 791× smaller — with the answer correct
and no page boilerplate (`Jump to content`, `Retrieved from`, `[edit]`) anywhere in the
history.

It fetches, strips to text, and has a small model answer your question over the content.
You get the answer, not the page.

---

## 6. Structured output — and a trap worth knowing about

`poc/20_structured_output.py`, `poc/results_structured_hallucination.json`.

Anyone wiring an agent into a service wants typed data, not prose. There are two
routes, and **they behave completely differently.**

### The supported route works

```python
class IncidentReport(BaseModel):
    totals: list[ServiceTotal]
    worst_service: str
    worst_minutes: int
    confidence: Literal["high", "medium", "low"]

result = agent(TASK, structured_output_model=IncidentReport)
report = result.structured_output      # a validated IncidentReport
```

It ran the tools, read the files, computed in the sandbox, and returned **6/6 exact
figures** with the worst service correct.

### The deprecated route returns confident fiction

```python
report = agent.structured_output(IncidentReport, TASK)   # deprecated
```

This does **not** run the agent loop, so it never touches the tools. It answers from
nothing and fills the schema anyway. Three runs:

| trial | exact figures | service names that exist in the data | what it invented |
|---|---|---|---|
| 1 | 0/6 | 0/5 | AuthService, APIGateway, DatabaseCluster, CacheLayer, LoadBalancer |
| 2 | 0/6 | 0/1 | `<UNKNOWN>` |
| 3 | 0/6 | 0/1 | ServiceA |

**0/3 runs produced a single correct figure. 3/3 invented service names.** Every object
validated cleanly against the Pydantic model.

In fairness, the SDK does warn:

```
DeprecationWarning: Agent.structured_output method is deprecated. You should pass in
`structured_output_model` directly into the agent invocation.
```

So this is a signposted migration, not a hidden trap. But the failure mode is worth
writing about: the deprecated path fails **silently and plausibly** rather than raising.
A validated object is not a correct one, and a Pydantic model cannot tell you the agent
never looked at your data.

**Practical rule for the article: pass `structured_output_model=` into the call. Never
use the standalone method.**

---

## 7. The other three ways to hold the leash

`poc/19_intervention_modes.py`. Only Cedar had been tested. Two custom tools were
registered — a harmless `read_report` and an irreversible `wire_money` — and the agent
asked to call both. Module-level counters record what actually executed, so a handler
that simply blocks everything cannot pass as a success.

| mode | harmless call ran | money transfer ran |
|---|---|---|
| none (control) | yes | **yes** |
| `"smart"` (LLM risk classifier) | yes | **no** |
| natural-language policy | yes | **no** |

The natural-language policy was literally this sentence:

> Read-only operations are always fine. Never permit anything that moves money,
> transfers funds, or has irreversible external side effects.

Both gated modes discriminated correctly: they let the benign call through and stopped
the destructive one. The control proves the gates did the work rather than the model
declining on its own.

This is the most quotable thing in the permissions story — you write the rule in
English and it becomes the standard each tool call is judged against.

**Observed wart:** teardown of an agent with MCP servers sometimes logs
`RuntimeError: Event loop is closed` and a `coroutine 'MCPClient.stop...' was never
awaited` warning. Cosmetic in these runs, but noisy in logs.

---

## Still to do for article 3

1. **An MCP server over HTTP/SSE**, not just stdio — transport coverage.
2. **Multiple MCP servers at once**, to show namespacing preventing a real collision.
3. **`mcp_router`** vended tool — untested, and it may matter for large server counts.
4. **`Agent.as_tool()`** — described from the README, never run.
5. **`make_subagent`** with presets and `Fixed`/`Inherit`/`Open`/`Choice` axes — untested.
6. **A skill with bundled scripts** the agent actually executes — only a prompt-only
   skill was tested.
8. **Sessions across a process restart** — only tested across agent objects in one process.
