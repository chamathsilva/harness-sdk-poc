<!--
Article 1 — full text, copied from the working doc so it lives with the evidence.
Source: https://claude.ai/code/artifact/e0d7ce0d-b5f9-4961-b48d-d3ec93f05a35 (rev 55, 2026-09-23)
Status: restructured and fact-checked; length decision pending (4,076 words of prose, ~17 min, vs a 3,500 target).
The doc is the working copy; if the two diverge, re-export from the doc.
Every number traces to FINDINGS.md; critical-claim wording follows the register in ARTICLE-SERIES.md.
-->

# Strands Harness, Hands-On: What AWS's New Agent Harness Actually Does

*What's in the box, what holds up when you measure it, and what to change before you trust it with anything real.*

On 21 September 2026 the Strands team at AWS released Strands harness: an open-source agent you get in one function call, under the Apache-2.0 licence. The launch post pitches it at builders who wish their Claude Code or Codex setup could run in the cloud, and calls it "a general-purpose agent rather than a coding agent." It also claims the harness costs 28% less than other harnesses across six benchmarks, and 77% less than Claude Code on Terminal Bench 2.1 with the same model. Those are the vendor's numbers. I didn't try to reproduce them.

What I did instead was build against it for a few days and turn every claim in this article into an experiment: more than 200 agent runs, each with a control where one made sense. Here's what it is, what comes in the box and how each part behaved when I ran it, where it bit me, and what I'd change before pointing it at anything real.

## What a harness actually is

If you have ever built anything with an AI model, you have written a harness. It is the loop that sends your prompt, reads what the model asked for, runs it and feeds the result back. It is also the counter that stops the loop spinning forever, and the decision, every turn, about what goes into the next message.

The model is the engine. The harness is everything bolted around it so the engine pulls in a useful direction. The word is borrowed from horses, and it is the right image: the animal supplies the power, and the harness turns it into a ploughed field rather than a hole in your fence.

The loop itself is a weekend's work. What comes after is the hard part: long conversations where the model loses the plot, a tool that returns 200KB and knocks everything over, an action nobody approved, a bill four times your estimate. Those are harness problems, and until recently everyone solved them privately.

## Meet Strands harness

Two names are worth keeping apart. *Strands harness* (`pip install strands-harness`) is the assembled agent. It is built on the *Strands Harness SDK*, published on PyPI as `strands-agents` and public since May 2025, which supplies the loop, the tools, the multi-agent patterns and the rest. The harness is the SDK with the decisions made for you. Here is the whole thing:

```python
from strands_harness import create_harness

agent = create_harness(model="anthropic/claude-haiku-4-5-20251001")
agent("Find the slowest test in this repo and explain why it's slow")
```

Leave `model` out and it defaults to Claude Opus 5 on Amazon Bedrock, which needs AWS credentials. The source knows seven providers: Bedrock, Bedrock Mantle, Anthropic, OpenAI, Google, Ollama and LiteLLM, plus any model object you build yourself. I ran two. Every number in this article is Anthropic; Bedrock was only for early runs.

That agent is meant to go and look: list files, open the relevant ones, run the tests, read the timings, answer. You don't give it tools or write a prompt, because both come with it.

There is a TypeScript twin (`@strands-agents/harness`, Node 22 or later), and a terminal command built on it:

```bash
npm install -g @strands-agents/cli
strands "summarize what this repo does"    # answer, then keep chatting
strands -p "list the top-level modules"    # one answer and exit
```

Inside the CLI, `/export` writes the agent you have set up out as Python or TypeScript. I didn't test the TypeScript package or the CLI. Everything below is Python.

## Twelve tools, and what they're for

That one call registers twelve tools. Grouped by job:

| Group | Tools | What they do |
| --- | --- | --- |
| Hands | `read`, `write`, `edit`, `shell`, `web_fetch` | Open files (images and PDFs too, where the model can see them), create and change files, run commands, read web pages |
| Orchestration | `programmatic_tool_caller`, `subagent`, `todo_write`, `strands_manage_background_task` | Write code that calls the other tools, delegate to a helper agent, keep a checklist, manage background work |
| Context and memory | `retrieve_context`, `retrieve_offloaded_content`, `search_memory` | Fetch back content moved out of the conversation; search long-term memory |

Web search is there too, but it doesn't show up in that list. On Anthropic, OpenAI and Google models it is the provider's own search, switched on as a model setting.

The third group is the telling one. Two of those tools exist to fetch back content the harness moved out of the context window; the third searches long-term memory. Each arrives with the feature that needs it, and switching the feature off removes the tool. They only make sense once you see what an agent is up against.

## The desk

An AI model has no memory. Every time it replies, the entire conversation so far is sent to it again from scratch, and that re-reading has a hard ceiling: the context window. Think of it as the desk the model works at. Everything it needs has to fit on the desk at once: your question, every file it has opened, every command's output.

Watch an agent work and the desk fills up. A config file, four hundred lines of test output, six source files. Forty minutes in, the thing it needs is somewhere under the pile. That is how agents actually fail: not with a dramatic wrong answer, but by slowly suffocating. And you are billed for everything on the desk on *every single turn*.

Throwing old things away destroys information the agent may still need. So the harness does four other things instead.

**It files bulky results instead of binning them.** A large tool result is cut down to a preview, and the full version is kept where the agent can fetch it back. I pointed an agent at a 400KB file. With context management on (the default), its conversation stayed at 9,928 characters. With it off, 175,317.

**It summarizes as it goes.** Tool results over about 1,500 tokens are cut to a preview straight away. Once the conversation passes 85% of the window, older exchanges get condensed. To watch this fire without paying for a full window, I shrank the window the manager measures against and lowered the trigger. Six turns later, 14 messages had become 4, and the agent still answered a question about the first turn correctly.

**It reads web pages somewhere else.** `web_fetch` does not paste a page into the conversation. It fetches the page, strips it to text, and asks a small, cheap model to answer your question from it. A 1.4MB Wikipedia page came back as an 1,800-character conversation, 791 times smaller, with the answer right and none of the page's boilerplate.

**It writes code, or it sends someone else.** These two are big enough for their own sections.

## The experiment that changed my mind

Normally an agent uses a tool by asking. It says "read this file," the file comes back, it thinks, it asks for the next one. Forty files means a lot of back-and-forth, and every file lands on the desk.

The `programmatic_tool_caller` tool offers a different deal: the agent writes a small program instead.

```python
totals = {}
for name in filenames:
    record = await read(path=f"/data/{name}")
    totals[record["service"]] = totals.get(record["service"], 0) + record["downtime_minutes"]
print(totals)
```

The program runs, calls `read` forty times by itself, and only what it prints comes back. The forty files never touch the desk. The agent gets six numbers.

The program runs in a real sandbox, called Monty, which matters when the code was written by an AI and is running on your machine. I spent a while trying to break out of it — opening files, importing `os`, opening a socket, the `__import__` trick that defeats most homemade sandboxes. Every attempt failed, and the way it failed is the interesting part: `socket` and `subprocess` raise *ModuleNotFoundError*, and `__import__` raises *NameError*. These are not blocked escape routes. They are absent. The only way out is the tools you handed in.

One thing to be clear about: Monty contains the code the agent writes in this mode, and nothing else. `shell` and the file tools run somewhere else entirely, by default on your own machine. More on that below.

I set this up expecting to measure money. I gave it forty incident records and asked for total downtime per service — a question with one correct answer I could check against.

Then I ran it thirty-nine times, because one run of a non-deterministic system is an anecdote.

### The thing I was not looking for

Asking one tool call at a time got all six numbers right **4 times out of 20**.

Writing a program got them right **18 times out of 19**. When a new release came out mid-test, I re-ran the small-data case twelve times each way: 4 out of 12, against 10 out of 12.

That is not a rounding difference, and it is worth being clear about what failure looks like here. The agent does not announce that it is struggling. It confidently names the right worst-offending service, formats a tidy list, and gets individual figures wrong by fifty or a hundred. It looks exactly like a correct answer.

My first thought was that I had rigged it. I had turned the model's reasoning off to keep costs down, which is precisely the setting that would hurt an agent doing sums in its head while leaving the program-writing arm untouched. So I ran it again with reasoning on.

It didn't close the gap. Adding up forty numbers scattered through a long conversation is the wrong job for a language model, and exactly the right job for four lines of Python.

### The money, which was the point originally

Cost turned out to be the smaller story, and it cuts both ways:

| Billable input, median | 40 small records | The same 40, now bulky |
| --- | --- | --- |
| Asking one call at a time | **12,244** | **106,664** |
| Writing a program | 23,749 | 28,912 |

On small data the program costs about twice as much: writing code costs more than just asking, and the model already batches its requests rather than trickling them out one by one. On bulky data it is nearly four times cheaper, because the data never reaches the desk at all.

### The part that should make you cautious

Code mode is not reliably cheap. In roughly one run in ten, 4 of 36 across both datasets, the model abandoned the sandbox partway and read every file itself. On the bulky data those runs cost a median of 469,484 tokens, against 26,650 for runs that stayed in the sandbox: about 17 times as much.

The worst cost **519,657 tokens**, five times more than never having the feature, and got every figure wrong. But half the runs that fell back still got every figure right. Falling back is reliably expensive, not reliably wrong.

So the honest summary is not "code mode is better." It is that **handing arithmetic to a program instead of a language model makes it correct**, that this is cheap on big data and dearer on small, and that every so often the model does not take the deal. Why it walks away, and what that does to your bill, gets an article of its own.

## Sending someone else

The `subagent` tool hires help: a second agent with a clean desk, given one task, returning only its conclusion. I tested whether the delegate's work really stays on *its* desk by stamping every record with a unique marker and counting how many reached the parent. Delegating: zero. Doing the job itself: 2,400.

The same idea comes in other shapes. `Agent.as_tool()` turns any agent into a tool another agent can call, starting from a clean conversation each time. `make_subagent()` builds a delegation tool from presets, and only the settings you leave open show up as parameters the model can set. Either way, a delegate inherits its parent's permissions and cannot be given tools the parent lacks.

For fixed pipelines, the SDK underneath has `Graph` and `Swarm`. I raced them against a single agent, five runs each. The graph wasn't reliably cheaper: on one task it was slightly cheaper, on another it cost almost five times as much. But it was the most predictable. Its best and worst runs stayed within about seven times of each other, where a single agent's once spread 119 times. That trade gets its own article too.

## It remembers you

Three kinds of memory come switched on, and they are worth telling apart.

**The conversation** is saved as it happens, under `./.agent/sessions`. Hand back its id to pick it up later:

```python
agent = create_harness(session={"id": "user-42"})
agent("Where did we leave off?")
```

I checked that this survives more than a new Python object. One process told an agent a fact and exited. A second process, started fresh with the same session id, restored the conversation and recalled the fact.

**Long-term memory** is the more interesting one. Every few turns, a small, cheap model reads back over what was said and pulls out things worth keeping: that you prefer a particular library, that a service belongs to a certain team. I tested it by telling an agent an invented codeword, throwing that agent away, and building a fresh one over the same folder. It knew the codeword. What it had written was a single readable line in a markdown file, 73 characters long. One catch: extraction runs in the background, so a short run can end before its last turns are saved.

**Skills** are how you teach it something. A skill is a folder with a `SKILL.md` inside: a name, a description, and instructions in plain English. Drop it in and the agent finds it.

```
.agent/skills/
└── release-notes/
    └── SKILL.md
```

It sees only the name and description up front and reads the full instructions when the job calls for it — the desk problem again, so twenty skills do not crowd out the work. I checked this was real rather than coincidence by inventing a house format no model would produce on its own, then asking a question that never mentioned the skill. With the folder present the agent followed the format. With it removed, it did not.

The thread running through all three is worth noticing. Everything lands as readable files in a folder in your project. Not a database, not a hosted service, not a vector store needing an account. If the agent has learned something wrong about you, you open the file and delete the line.

## Plugging in your own things

The built-ins are a starting point, and what you add is treated the same way.

**Your own tools.** A plain Python function with a `@tool` decorator is registered and callable by the model. It is also callable from inside the code-mode sandbox, like any built-in, and governed by the same permission policy as `shell`. I gave an agent a destructive custom tool and a policy that forbade it. The call was refused, and a counter inside the function confirmed it never ran.

**MCP servers.** Point it at a Model Context Protocol server and its tools appear, prefixed with the server's name so they can't collide. One filesystem server gave the agent 14 tools, which it used without being told to. A broken server alongside it didn't take the agent down; the working server's tools still worked. Servers over HTTP work as well as local ones.

**Typed answers.** Pass a Pydantic model as `structured_output_model=` and you get a validated object back instead of prose. It ran the tools, did the sums and filled the schema correctly in 3 runs out of 3. There is an older way to do this that behaves very differently; see *What surprised me*.

## The leash

Go back to that three-line example. The agent it creates can run any shell command and write to any file, and it will do so without asking. That is the default.

On a laptop, in a scratch folder, fine. Pointed at anything real, that should give you pause.

There are four ways to hold the leash, and a Cedar policy can be layered with any one of the other three:

```python
create_harness(interventions="ask")     # ask me before every action
create_harness(interventions="smart")   # judge each action, ask only about risky ones
create_harness(interventions="Read-only, but writing under ./out is fine")
create_harness(interventions="./agent.cedar")   # a formal written policy
```

The third deserves a second look: you write the rule in ordinary English, and it becomes the standard each action is judged against.

The fourth is the serious one. Cedar is Amazon's policy language, the same sort of thing that governs who can touch what in cloud infrastructure. Using it here means your agent's permissions are written down and reviewable like any other config, rather than hopefully-worded pleading inside a prompt.

Mine was four lines. Read a file in the incidents folder: allowed. Anything else: refused.

```
permit(principal, action == Action::"programmatic_tool_caller", resource);

permit(principal, action == Action::"read", resource)
when { context.input.path like "*/data/incidents/*" };
```

### The question worth asking

Here is what I actually wanted to know. The agent can write and run its own code. So what stops it writing code that reads the file the policy forbids?

This is not paranoia. A sandbox that could reach around your security rules would be a hole straight through them, and it is an easy mistake for a library to make.

So I told the agent to try it: from inside its sandbox, read one permitted file and one forbidden one.

```
ALLOWED_READ: ok
FORBIDDEN_READ: blocked -> RuntimeError("Tool 'read' error:
                DENIED: Access denied by Cedar policy")
```

The rule held. Calls made from inside the sandbox pass through the same checkpoint as everything else. The same is true of work handed to a subagent: a delegate cannot be given permissions the agent that summoned it does not already have.

That is the most reassuring thing I found all day, and it is written down. The documentation for `create_harness` says a subagent inherits the policy "so a delegate cannot bypass it."

## Seeing what it did

Tracing is built in and off by default. Set the standard OpenTelemetry variable, `OTEL_TRACES_EXPORTER=console` (or `otlp`, to send spans to a collector), and every agent call, loop cycle, model call, tool call and delegation becomes a span. With the variable unset I got no spans. With it set, one small delegated task produced 16.

## The prompt in the box

Every agent has a system prompt: standing instructions the model reads before anything else. Strands ships theirs as a documented, importable part of the library:

```python
from strands_harness import HARNESS_CONTRACT
```

It is 1,665 characters, and it is the most quietly interesting file in the project. Some of what it tells the model:

> Keep working until the task is fully resolved before ending your turn. Only stop to ask the user when you are blocked on a decision or information that is genuinely theirs to provide.

> Once you have enough to act on, act. Do not ask for confirmation of steps you can verify yourself.

> Treat a task as done only when you have verified it, not when it looks plausible. If you cannot verify, say so.

> A denied or failed tool call is information: adjust your approach, do not retry it verbatim.

Read that list again as a catalogue of the ways agents annoy people. They stop halfway to ask permission for something they could have checked. They declare victory without testing. They retry the same failing command.

Every line is a scar. Somebody got burned, and the fix went into the box.

Notice what is *not* in there: no name, no personality, no domain. The contract says nothing about who the agent is or what it is for. That part is yours:

```python
create_harness(instructions="You are a support assistant. Always link the ticket you're working on.")
```

The split is deliberate. They ship the hard-won behaviour; you bring the job.

## What surprised me

**The token counter undercounts.** On the Anthropic API, a run's `totalTokens` leaves out tokens read from or written to the prompt cache, and most of an agent's input is cache. On one small cached run it reported a total of 138 tokens, when the input alone was 12,510. It is a known, open issue ([#3546](https://github.com/strands-agents/harness-sdk/issues/3546)). If you track cost, add `cacheReadInputTokens` and `cacheWriteInputTokens` to `inputTokens`.

**A validated object is not a correct one.** Before `structured_output_model=` there was `agent.structured_output()`. It is deprecated, and it does something narrower than it looks: it makes one model call that formats what the conversation already contains. Its documentation says it answers from the conversation history, and the source shows it runs no tools. Called after the agent had done the work, it was perfect, 3 runs out of 3. Called on a fresh agent with the task in the prompt, it returned objects that passed every schema check with every figure invented, 3 out of 3. Nothing about those objects looked wrong.

## Before you ship it

A few days of building against it turned up friction worth knowing about. None of it is fatal.

**The defaults are built for a developer's laptop.** Out of the box, `shell` and the file tools run on your machine with your privileges, and no call is gated: every permission option above is off until you pick one. The SDK is blunt about it. When no sandbox is configured, the execution environment is a class called `NotASandboxLocalEnvironment`, and its documentation says the name is a warning. Anything reachable from your shell is reachable by the agent, including cloud credentials sitting in a config file. Pass a Docker or SSH sandbox, or an interventions policy, before you point it at anything real, and give it a scoped key rather than your everyday one.

**Know your tools' habits.** `read` numbers its lines, like `cat -n`, so the model can cite `path:line`; code that parses file contents has to strip them. It also takes absolute paths and reads files, not folders. Listing directories is `shell`'s job, so if you remove `shell`, tell the agent exactly where things are.

**It is very new.** The harness went from 0.1.1 to 0.1.2 while I was testing, and the SDK from 1.56.0 to 1.57.0. The default reasoning setting changed along the way. Expect the surface to move. The upside is that the source is unusually well documented, and my best answers came from its docstrings.

**Web search depends on the model.** Where the provider has its own search, it is switched on. Elsewhere it is off, unless you opt into Exa's hosted search, which works on any model since 0.1.2 and sends your queries to a third party.

## So should you use it?

**If you are about to write your own agent loop, try this first.** The loop is a weekend. Everything after it — keeping the desk clear, remembering across sessions, deciding what the agent may touch — is months, and it is all here.

**If you already have an agent in production,** the piece worth stealing is the permissions layer, even if you take nothing else. Written-down rules that hold even when the agent writes its own code are hard to build and easy to get subtly wrong.

**If you are shipping to customers next month,** wait a little. Version 0.1.2 is days old. Use the SDK underneath, which is at 1.57.0 and has been public since May 2025.

**If you are just curious,** install the terminal command and point it at a repo you know well. Ten minutes will teach you more than this article.

### The part that stays with me

A framework's defaults are an argument about what matters, and you can read them like one.

This one turns on, by default: a prompt that says verify before you claim you are done; tools that fetch back what the agent had to set aside; memory that writes itself into files you can edit; a summarizer that keeps long work coherent.

It leaves off, by default: asking your permission.

That combination tells you exactly what the last two years taught this team. Getting a model to do useful work is close to solved. Keeping it coherent over a long task, and keeping it affordable, is not — so that is where nearly all the machinery points.

The permissions question they answered thoroughly and then shipped switched off. They are honest about it, since the default environment's name is a warning label, but I still think it is the wrong default. Nobody wants their quickstart to open with a permission prompt. I would still rather see one than hand an agent my shell.

But the shape of the thing is right, and my measurements kept pointing the same way. The agent got more reliable every time a decision was taken away from the model and given to something deterministic: arithmetic to a program, fixed steps to a graph, permissions to a written policy. The next articles take those one at a time.

---

*The project is at [github.com/strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk), Apache-2.0. Everything here comes from more than 200 agent runs on synthetic data, first against `strands-harness` 0.1.1 and re-checked on 0.1.2 (SDK 1.56.0 and 1.57.0), with reasoning off unless stated. The code and a log of every measurement are at [github.com/chamathsilva/harness-sdk-poc](https://github.com/chamathsilva/harness-sdk-poc). I didn't reproduce the vendor's benchmark claims. One caveat worth stating plainly: all of it ran on Claude Haiku 4.5, a small, fast model. The accuracy gap is the finding I would most want to re-check on a frontier model before assuming it holds everywhere.*
