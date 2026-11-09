"""A span as plain data: easy to save, load, filter and test.

OpenTelemetry's own span objects are rich but awkward to query. SpanRecord keeps
only what an analysis needs. Task 2 works on lists of SpanRecord.
"""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    parent_id: str          # "" for the root span of a trace
    name: str
    status: str             # "UNSET", "OK" or "ERROR"
    attributes: dict = field(default_factory=dict)
    start_ns: int = 0
    end_ns: int = 0

    @property
    def duration_ms(self) -> float:
        return (self.end_ns - self.start_ns) / 1e6

    def attr(self, key, default=None):
        return self.attributes.get(key, default)

    @staticmethod
    def from_otel(span) -> "SpanRecord":
        ctx = span.get_span_context()
        return SpanRecord(
            trace_id=format(ctx.trace_id, "032x"),
            span_id=format(ctx.span_id, "016x"),
            parent_id=format(span.parent.span_id, "016x") if span.parent else "",
            name=span.name,
            status=span.status.status_code.name,
            attributes=dict(span.attributes or {}),
            start_ns=span.start_time,
            end_ns=span.end_time,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def load_jsonl(path) -> list:
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"No trace file at {path}. Run `python3 main.py` first.")
    return [SpanRecord(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line]
