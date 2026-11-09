"""Build the OpenTelemetry pipeline:  tracer -> span processors -> exporters.

    JSONL file     always: traces/latest.jsonl, read by analyze.py
    OTLP           with --otlp: LangSmith, or any OTLP backend (Langfuse, Jaeger, Phoenix)
    extra          tests pass an in-memory exporter here

The OTLP exporter takes its settings from environment variables (put them in .env):

    OTEL_EXPORTER_OTLP_ENDPOINT   base URL; the exporter adds /v1/traces itself
    OTEL_EXPORTER_OTLP_HEADERS    for LangSmith: x-api-key=...,Langsmith-Project=...

Switching backend means changing these two lines. The agent code does not change.
"""
import os

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from tracing.file_exporter import JsonlFileExporter

SERVICE_NAME = "trip-claim-agent"


def build_tracing(trace_file=None, otlp=False, extra_exporter=None):
    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    if trace_file:
        provider.add_span_processor(SimpleSpanProcessor(JsonlFileExporter(trace_file)))
    if otlp:
        provider.add_span_processor(BatchSpanProcessor(_otlp_exporter()))
    if extra_exporter is not None:
        provider.add_span_processor(SimpleSpanProcessor(extra_exporter))
    return provider, provider.get_tracer("mai580.observability.lab")


def _otlp_exporter():
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        raise SystemExit("--otlp needs OTEL_EXPORTER_OTLP_ENDPOINT. Copy .env.example to .env "
                         "and paste your LangSmith API key (README, Task 4).")
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    except ImportError:
        raise SystemExit("Missing package: pip install -r requirements.txt")
    return OTLPSpanExporter()   # reads the endpoint and headers from the environment
