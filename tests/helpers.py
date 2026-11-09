"""Run the agent with an in-memory exporter, so tests can inspect every span."""
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from agent import ReplayModel, ToolRunner, TripClaimAgent, load_claims
from tools import PaymentGateway, build_tools
from tracing import ContentPolicy, SpanRecord, Spans, build_tracing


def run(claim_ids=None, capture="SPAN_ONLY"):
    """Returns (records, answers, gateway)."""
    memory = InMemorySpanExporter()
    provider, tracer = build_tracing(extra_exporter=memory)
    spans = Spans(tracer, ContentPolicy(capture))
    gateway = PaymentGateway()
    agent = TripClaimAgent(ReplayModel(), ToolRunner(build_tools(gateway), spans), spans)
    answers = {c.id: agent.run(c) for c in load_claims(claim_ids)}
    provider.shutdown()
    return [SpanRecord.from_otel(s) for s in memory.get_finished_spans()], answers, gateway


def span(trace, span_id, name, parent="", status="UNSET", **attributes):
    """Build one SpanRecord by hand (Task 2 tests)."""
    attrs = {k.replace("__", "."): v for k, v in attributes.items()}
    return SpanRecord(trace_id=trace, span_id=span_id, parent_id=parent, name=name,
                      status=status, attributes=attrs, start_ns=int(span_id, 16), end_ns=int(span_id, 16) + 1)


def agent_span(trace, claim_id):
    return span(trace, "0001", "invoke_agent trip-claim-agent",
                gen_ai__operation__name="invoke_agent", app__claim__id=claim_id)


def tool_span(trace, span_id, tool, call_id, status="UNSET"):
    return span(trace, span_id, f"execute_tool {tool}", parent="0001", status=status,
                gen_ai__operation__name="execute_tool", gen_ai__tool__name=tool, gen_ai__tool__call__id=call_id)
