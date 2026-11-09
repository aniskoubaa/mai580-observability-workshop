"""The harness: it runs the tool calls the model asks for.

It retries once when a tool times out. That looks like good engineering.
Keep this file open during Task 0: is the retry safe for every tool?
"""
from agent.replay_model import ToolCall


class ToolRunner:
    MAX_ATTEMPTS = 2

    def __init__(self, tools: dict, spans):
        self.tools = tools
        self.spans = spans

    def run(self, call: ToolCall) -> dict:
        tool = self.tools.get(call.name)
        if tool is None:
            return {"error": f"unknown tool {call.name}"}

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                with self.spans.tool(call, tool) as span:      # Task 1 writes this span
                    result = tool.fn(**call.arguments)
                    self.spans.tool_result(span, result)
                    return result
            except TimeoutError as exc:
                if attempt == self.MAX_ATTEMPTS:
                    return {"error": f"TimeoutError: {exc}"}
                # try again: the model never hears about the first attempt
            except Exception as exc:
                return {"error": f"{type(exc).__name__}: {exc}"}
