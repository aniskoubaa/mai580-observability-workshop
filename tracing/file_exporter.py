"""An OpenTelemetry exporter that writes each finished span as one JSON line.

An exporter is the last step of the pipeline: tracer -> span processor -> exporter.
LangSmith's exporter sends spans over the network (OTLP). This one writes a file,
so you can read and query your traces with no account and no internet.
"""
from pathlib import Path

from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from tracing.records import SpanRecord


class JsonlFileExporter(SpanExporter):
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")      # one run per file

    def export(self, spans) -> SpanExportResult:
        with self.path.open("a", encoding="utf-8") as f:
            for span in spans:
                f.write(SpanRecord.from_otel(span).to_json() + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass
