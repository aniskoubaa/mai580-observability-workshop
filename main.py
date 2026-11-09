"""Run the trip-claim agent on the six claims and trace every step.

    python3 main.py                        all claims; print the traces as trees
    python3 main.py --claim C-104          one claim
    python3 main.py --capture SPAN_ONLY    also record content (prompts, tool input/output)
    python3 main.py --otlp                 also send the spans to LangSmith (settings in .env)
    python3 main.py --quiet                no trees, only the summary

Every run writes traces/latest.jsonl. Query it afterwards with `python3 analyze.py`.
"""
import argparse
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_dotenv(path=HERE / ".env"):
    """Read KEY=VALUE lines from .env into the environment (no package needed)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_dotenv()      # before OpenTelemetry reads its OTEL_* variables

    from agent import ReplayModel, ToolRunner, TripClaimAgent, load_claims
    from tools import PaymentGateway, build_tools
    from tracing import ContentPolicy, Spans, build_tracing, load_jsonl
    from tracing.tree_view import bold, dim, green, print_traces, red

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--claim", action="append", help="run only this claim (repeatable)")
    p.add_argument("--capture", choices=["NO_CONTENT", "SPAN_ONLY", "EVENT_ONLY", "SPAN_AND_EVENT"],
                   help="content capture mode (default: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT, "
                        "else NO_CONTENT)")
    p.add_argument("--otlp", action="store_true", help="also export to the OTLP endpoint in .env")
    p.add_argument("--quiet", action="store_true", help="do not print the trace trees")
    args = p.parse_args()

    trace_file = HERE / "traces" / "latest.jsonl"
    provider, tracer = build_tracing(trace_file=trace_file, otlp=args.otlp)
    content = ContentPolicy(args.capture)
    spans = Spans(tracer, content)
    gateway = PaymentGateway()
    agent = TripClaimAgent(ReplayModel(), ToolRunner(build_tools(gateway), spans), spans)

    claims = load_claims(args.claim)
    answers = {c.id: agent.run(c) for c in claims}
    provider.shutdown()            # flush: the OTLP exporter sends in batches

    if not args.quiet:
        print(bold("Traces") + dim(f"  (content capture: {content.mode})"))
        print_traces(load_jsonl(trace_file))

    print("\n" + bold("What the agent said") + "                              " + bold("What finance sees"))
    for c in claims:
        paid = gateway.payments_for(c.id)
        mark = green("ok") if paid == c.expected_payments else red(f"expected {c.expected_payments}")
        print(f"{c.id}  {answers[c.id][:52].ljust(52)}  payments: {paid}  {mark}")

    print(dim(f"\nSpans saved to {trace_file.relative_to(HERE)}. Next: python3 analyze.py"))
    if args.otlp:
        print(dim("Spans sent to " + os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]))


if __name__ == "__main__":
    main()
