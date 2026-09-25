<!--
Article 1 — revised draft under ARTICLE-PLAN.md and ARTICLE-1-OUTLINE.md.
The prior draft is preserved in archive/ARTICLE-1-PREVIOUS.md.
Publication review is in ARTICLE-1-REVIEW.md. Do not reintroduce the earlier exact
accuracy tallies until their saved answers and scoring have been audited.
-->

# Strands Harness in Practice: What It Handles and What You Still Control

*A practical look at its tools, context, memory, and permissions, with experiments behind the advice.*

Give an agent a folder of incident reports and ask which service lost the most time. The request sounds small. The agent has to find and read the files, calculate totals, and give you an answer you can check. If you want to continue tomorrow, something has to preserve the conversation. Before it starts, you also have to decide which files and commands it may use.

Strands Harness assembles much of that machinery through `create_harness()`. I used synthetic incident data and focused experiments to examine what that saves an engineer. The benefit is a working starting point: tools, instructions, context management, and persistence already connected. The decisions that remain are about your application: what the agent may access, what it should remember, and how you will judge its answers.

## What one call assembles

An agent needs a loop around its model. The model asks to use a tool; the loop executes the call, returns the result, and decides what context to send on the next turn. A useful agent also needs instructions, a way to manage long conversations, somewhere to store state, and rules about what actions are allowed.

The [Strands Harness SDK](https://strandsagents.com/docs/user-guide/sdk/) supplies the pieces for building that system. [Strands Harness](https://strandsagents.com/docs/user-guide/harness/) is an assembled version with choices already made, released by the Strands team at AWS in September 2026. Its Python package, `strands-harness`, returns an ordinary Strands `Agent`, so you can still change those choices or use the underlying SDK directly.

With the Anthropic extra installed and `ANTHROPIC_API_KEY` configured, a first invocation looks like this; the repository's [setup instructions](README.md) cover the environment. This default agent has host file tools and a shell, so use a workspace and credentials appropriate for that access.

```python
from strands_harness import create_harness

agent = create_harness(model="anthropic/claude-haiku-4-5-20251001")
agent("Summarize the incident in /absolute/path/to/INC-1001.json")
```

Replace that path with a file you control. Naming the model makes the provider and model choice explicit. This example uses the same Haiku model as the measurements below.

In an [inspection without model calls](poc/31_strands_surface.py) of version 0.1.2, the assembled agent exposed twelve registered tools. Some read and change files or run commands. Others let the model delegate work or write a small program that calls its tools. Three serve context and memory: two retrieve material moved out of the active conversation, and one searches long-term memory.

The assembly also includes a framework-written set of working instructions. You can append instructions for your domain; you do not have to author the tool loop or its general working prompt first. That is the immediate saving. It also means the defaults are consequential. A tool that is present can be chosen by the model, and a memory feature that is on can write information beyond this turn.

I inspected that assembled agent, but most behavioral experiments deliberately selected fewer tools or disabled memory and sessions to isolate one mechanism. Those experiments tell us what individual parts did under a stated configuration. They are not a benchmark of the entire default agent.

## What happens as work accumulates

An agent's active conversation is a desk with limited space. A file returned by a tool goes onto that desk, and the model may see it again on later turns. Large results leave less room for the question, the agent's prior work, and the next result. The harness manages this by replacing some bulky tool output with a short preview and a way to retrieve the rest. It can also summarize older conversation when the working context grows.

I [tested offloading](poc/10_offloading.py) by asking an agent to read a large text file, once with the context manager on and once with it off. The serialized conversation measured **9,928 characters** with management on and **175,317** with it off. These counts measure text retained in the conversation; they do not measure billed tokens. In both runs, `read` capped its response at 2,000 lines. Within that limit, enabling context management left far less text in the history. The [saved results](poc/results_offloading.json) show the comparison.

I also [tested summarization](poc/22_summarization.py) by lowering the configured context window and trigger threshold. After six supplied facts and a follow-up question, the managed history had four messages against fourteen with management off. Both agents still answered the question about the first fact. The [results](poc/results_summarization.json) demonstrate compaction under a forced trigger; the test did not measure when the default threshold would fire during ordinary use.

Keeping a conversation manageable is different from keeping it for later. A **session** saves the conversation so an agent can resume it by ID. To check that this was more than an object remaining in Python memory, I ran a [two-process experiment](poc/21_session_restart.py). The first process supplied an arbitrary bridge number and escalation owner, then exited. A new process loaded the same session ID, restored two earlier messages, and recalled both facts. That demonstrates a clean process restart in this setup; it does not test recovery from a crash during a write.

**Long-term memory** answers a different question: can a new conversation recall a fact from an earlier one? In a [separate test](poc/08_memory.py), one agent learned an invented codeword. I waited for its memory manager to flush, built a new agent over the same memory directory, and asked for the word and its owning team. Both came back. The stored fact was a readable Markdown file. Extraction runs in the background, so a short process that exits before the write finishes can leave its latest fact unsaved. For a deployed application, the default local directories for sessions and memory also need an appropriate durable location; the [production guidance](https://strandsagents.com/docs/user-guide/harness/production/) calls this out for ephemeral containers.

Those mechanisms solve different problems. Context management limits what the model carries on its desk now. A session continues one conversation later. Long-term memory can bring a selected fact into a new conversation. I would decide which of those an application needs before accepting all three as incidental defaults.

## How it gets the work done

The default tools let an agent read files, edit them, run commands, fetch web content, and delegate. The model can request several ordinary tool calls in one turn; forty files do not automatically mean forty separate model round trips. Strands also offers `programmatic_tool_caller`: the model writes a short Python program that calls its registered tools, processes their results, and prints only what the model needs to see next. The intermediate tool responses can stay inside that program instead of filling the conversation. The [official guide](https://strandsagents.com/docs/user-guide/harness/tools/programmatic-tool-calling/) describes that contract.

This matters for the incident task. Each record has a service and a downtime value. A program can read the records, add the numbers by service, and print six totals. The model then receives the result of the calculation without carrying every intermediate record into its next turn. Parsing is part of that work: Strands `read` returns tool content with numbered lines, which the program must handle before treating the file contents as JSON.

I compared a restricted agent with `read` against one with `read` plus code mode. Both got the same task and files within each dataset. Memory, sessions, skills, and context management were off so they would not cloud the comparison. That is a test of orchestration choices, not of the default assembled harness. The small and bulky datasets were also generated independently, so they are two workload shapes, not identical incidents with extra text attached.

The [recorded calls](poc/results_codemode_diagnostic.json) show why actual behavior needs inspection. In one instrumented run on bulky records, the model made forty direct `read` calls as well as five calls to the code tool. Enabling code mode had not kept all the file processing inside it. If your reason for choosing code mode is to keep intermediate data out of the conversation, check the tool trace to see whether the agent actually followed that route. The [benchmark script](poc/02_context_economics.py) makes the restricted configuration explicit.

Delegation offers another way to keep a large task out of the parent's active conversation. I gave a helper the bulky incident files, each containing unique trace markers, then counted those markers in the parent's history. With the built-in `subagent`, the parent had **zero** of the 2,400 markers. When the parent read the files itself, its history contained **all 2,400**. That [marker experiment](poc/07_subagent_isolation.py) demonstrates context separation for this route. It is not a general confidentiality guarantee: a delegate may still return sensitive information in its conclusion if the task asks for it.

Code mode and delegation are useful because they change where the working material goes. Whether either makes your task more accurate or economical depends on the task, the model, and the choices the agent actually makes. Their traces and final answers need checking against a known result.

## What it can touch

To understand the agent's access, follow a call from the model to the resource it reaches. Model-written code in `programmatic_tool_caller` runs in Monty, an isolated Python interpreter. Calls from that program to `read` or `shell` pass through the normal tool executor. The tool's **execution environment** determines where the file is read or the command runs. By default, those tools run on the host. An OS boundary around them requires a separately configured environment, as the [production guidance](https://strandsagents.com/docs/user-guide/harness/production/) explains.

I drove Monty directly in a [boundary test](poc/06_sandbox_boundary.py). Attempts to open a host file, inspect environment variables, start a process, and reach the network failed in that test. A control calculation returned `45`, proving the code tool was actually executing the submitted program. That is evidence for the attempted paths in the tested release; it is not a proof that every possible escape has been excluded. I did not test a Docker or SSH execution environment around the host tools.

**Authorization** adds a decision before execution. Strands accepts an [intervention policy](https://strandsagents.com/docs/user-guide/harness/configure/interventions/) that decides whether a tool call may run; the default applies no such gate. Calls made from code mode pass through it too. In my [path experiment](poc/03_interventions.py), a Cedar policy permitted a read matching an incident path and denied a vault path. The agent reported the expected results, although that test graded its report rather than independently inspecting the file access.

A [custom-tool experiment](poc/17_custom_tools.py) added an execution counter. I registered a working lookup tool and a simulated deletion tool whose body incremented a counter without deleting anything. The lookup ran in a separate registration check. With a Cedar policy that omitted permission for deletion, the agent reported a denial and the deletion counter stayed at **zero**. That independently confirmed the function had not executed in the denied run.

Here is the configuration used for the narrower path test, expressed relative to this repository's root:

```python
from strands_harness import create_harness

agent = create_harness(
    model="anthropic/claude-haiku-4-5-20251001",
    effort="off",
    builtin_tools=["read", "programmatic_tool_caller"],
    interventions="poc/agent.cedar",
    memory=False,
    session=False,
    skills=False,
    builtin_plugins=[],
    context_manager=False,
)
```

The [policy file](poc/agent.cedar) permits the code tool and `read` calls whose path argument matches `*/data/incidents/*`; other actions receive Cedar's default denial. This is a pattern check on the supplied path. The experiment does not establish filesystem containment against alternative path spellings or symlinks. The example requires the Cedar dependency and builds on the tested 0.1.2 environment. Its disabled features isolate the policy test; they are not a general application preset.

For an application, choose the tools, policy, and execution environment together, then test allowed and denied actions. Human approval also affects the flow: inside code mode, a call requiring interactive approval raises an error the program can catch instead of pausing for input. The [code-mode guide](https://strandsagents.com/docs/user-guide/harness/tools/programmatic-tool-calling/) documents this behavior.

## Making it useful for your task

The factory accepts domain instructions and tools you write. A Python function decorated with `@tool` can be registered beside the built-ins. In the custom-tool experiment, the model called the function directly, and code mode could call it as an async tool too. Adding a function therefore adds real authority to the agent. Its name and description may help the model decide when to use it; its implementation and policy determine what it can actually do.

**Skills** supply task instructions from folders. I invented an incident-summary format, wrote it in a `SKILL.md`, and explicitly configured the agent to use its directory. The agent followed the format's markers despite a prompt that never mentioned them. With skills disabled as a control, it did not. This [one-format test](poc/09_skills.py) demonstrates use of a supplied skill; it does not establish how reliably the agent chooses among many overlapping skills.

**Model Context Protocol (MCP) servers** provide tools through a standard interface. In one [stdio test](poc/16_mcp.py), a filesystem server contributed fourteen tools with a server prefix in their names, and the agent used one to count the incident files. When I added a broken server beside it, the working server still contributed its tools. A separate [HTTP test](poc/25_mcp_http.py) exercised discovery and a call over that transport. Authentication and name collisions across many servers were outside those checks.

When an application needs a typed result, `structured_output_model=` can return an object validated against a Pydantic model. That is useful at the boundary with other software. A valid object still needs a factual check. In the [supported-route experiment](poc/20_structured_output.py), the agent had the tools needed for the task and the saved object could be compared with ground truth. I would perform that comparison for any field whose value matters; a schema only checks shape and types.

## How I would start

I would begin with a small task whose answer I can verify. For these incident files, I would calculate the service totals independently and compare every service/value pair in the agent's complete answer. I would also save its tool calls and usage, so a plausible answer could be checked against both the expected result and the work that produced it.

The first configuration decisions follow from that task. Name the model, select the necessary tools, and define the files or services they can reach. For a one-off calculation, decide whether anything needs to persist. For an ongoing incident assistant, test resuming a session and recalling a fact separately. Add capabilities one at a time so you can see what each changes in the answer and the retained context.

Strands Harness is worth evaluating when you want a working agent with these pieces assembled and still want to replace individual defaults. The SDK underneath is available when you need to construct those pieces more explicitly. The work that remains yours is concrete: choose the model, constrain its authority, decide what persists, and grade its answers against something outside the model's own account.

**Method.** The recorded experiments used Claude Haiku 4.5 through the Anthropic API, usually with `effort="off"`, on synthetic data. The original runs used `strands-harness` 0.1.1 and SDK 1.56.0; selected checks were repeated on 0.1.2 and SDK 1.57.0. Default-agent inspection, isolated capability tests, source reading, and the restricted tool benchmark are different forms of evidence. The [scripts and raw results](poc/) are in this repository. I did not reproduce the vendor's benchmark comparisons or evaluate a production deployment. These observations may change with another model, task, or release.
