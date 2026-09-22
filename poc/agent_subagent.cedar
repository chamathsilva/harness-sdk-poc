// Cedar is default-deny. The agent may delegate and may orchestrate with code,
// but reads are confined to the incidents directory -- for the parent AND,
// the docs claim, for any subagent it spawns.
permit(principal, action == Action::"subagent", resource);
permit(principal, action == Action::"programmatic_tool_caller", resource);

permit(principal, action == Action::"read", resource)
when { context.input.path like "*/data/incidents/*" };
