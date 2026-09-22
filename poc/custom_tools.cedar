// Your own tools become Cedar actions by their tool name, same as built-ins.
permit(principal, action == Action::"lookup_ticket", resource);
permit(principal, action == Action::"programmatic_tool_caller", resource);
// delete_everything is simply never permitted.
