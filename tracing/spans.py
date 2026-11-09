"""One method per kind of span. The agent and the harness call these; they never
touch OpenTelemetry directly. Span names and attributes follow the OpenTelemetry
GenAI semantic conventions (status: Development, so names may still change):

    invoke_agent {gen_ai.agent.name}     the whole claim          (written for you)
    chat {gen_ai.request.model}          one model call           (written for you)
    execute_tool {gen_ai.tool.name}      one tool attempt         <- TASK 1

TASK 1 — make tool calls visible.

Until you write `tool()`, it opens no span, so tool calls are invisible in the
trace. Write it so that each tool attempt becomes one span:

    name        "execute_tool " + call.name           e.g. "execute_tool read_receipt"
    kind        SpanKind.INTERNAL
    attributes  gen_ai.operation.name = "execute_tool"
                gen_ai.tool.name      = call.name
                gen_ai.tool.call.id   = call.id
                gen_ai.tool.type      = tool.type
                plus everything in self.tool_arguments(call)

If the tool raises an exception, set the attribute error.type to the exception's
class name (for example "TimeoutError") and raise it again. OpenTelemetry then
records the exception and marks the span status ERROR for you.

Read agent() below first: tool() has the same shape, plus a try/except.

Check your work:  python3 -m unittest tests.test_task1_tool_span
"""
from contextlib import contextmanager

from opentelemetry.trace import SpanKind

from tracing.content import ContentPolicy


class Spans:
    def __init__(self, tracer, content: ContentPolicy):
        self.tracer = tracer
        self.content = content

    # ---------- the whole claim: the root span of each trace ----------
    @contextmanager
    def agent(self, agent_name: str, claim_id: str):
        attributes = {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": agent_name,
            "gen_ai.conversation.id": claim_id,
            "app.claim.id": claim_id,            # our own attribute: "app." is not an OTel namespace
            "langsmith.span.kind": "chain",      # LangSmith-only hint; other backends ignore it
        }
        with self.tracer.start_as_current_span(f"invoke_agent {agent_name}", kind=SpanKind.INTERNAL,
                                               attributes=attributes) as span:
            yield span

    def agent_result(self, span, final_answer: str):
        span.set_attribute("app.claim.decision", final_answer.split()[0])   # APPROVE or REJECT
        span.set_attributes(self.content.capture("output.value", final_answer))

    # ---------- one model call ----------
    @contextmanager
    def chat(self, model, messages: list):
        attributes = {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": model.provider,
            "gen_ai.request.model": model.name,
            **self.content.capture("gen_ai.input.messages", messages),
        }
        with self.tracer.start_as_current_span(f"chat {model.name}", kind=SpanKind.CLIENT,
                                               attributes=attributes) as span:
            yield span

    def chat_result(self, span, reply):
        span.set_attribute("gen_ai.usage.input_tokens", reply.input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", reply.output_tokens)
        span.set_attributes(self.content.capture("gen_ai.output.messages", [reply.as_message()]))

    # ---------- one tool attempt: TASK 1 ----------
    @contextmanager
    def tool(self, call, tool):
        # TODO (Task 1): replace the line below with a span, as described at the top of this file.
        yield None

    def tool_arguments(self, call) -> dict:
        """Content attributes for the tool's input. Empty unless content capture is on.
        input.value is what LangSmith shows as the run's input."""
        return {**self.content.capture("gen_ai.tool.call.arguments", call.arguments),
                **self.content.capture("input.value", call.arguments)}

    def tool_result(self, span, result: dict):
        if span is None:          # Task 1 not written yet: nothing to record on
            return
        span.set_attributes({**self.content.capture("gen_ai.tool.call.result", result),
                             **self.content.capture("output.value", result)})
