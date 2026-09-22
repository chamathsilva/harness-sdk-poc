// Cedar is default-deny: anything not permitted here is refused.
// Each tool maps to a Cedar action; tool arguments arrive as context.input.

// The agent may orchestrate its tools with code.
permit(principal, action == Action::"programmatic_tool_caller", resource);

// ...but it may only read inside the incidents directory.
// Reads anywhere else (./data/vault, /etc, ~/.aws) fall through to the default deny.
permit(principal, action == Action::"read", resource)
when { context.input.path like "*/data/incidents/*" };
