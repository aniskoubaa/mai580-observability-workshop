"""Query saved traces: a metrics table, then the repeated-payment detector (Task 2).

    python3 analyze.py                         reads traces/latest.jsonl
    python3 analyze.py path/to/other.jsonl

Traces are data. This script never runs the agent: it only reads what was recorded.
"""
import sys
from pathlib import Path

from analysis import find_repeated_payments, per_claim_metrics
from tracing import load_jsonl
from tracing.tree_view import bold, dim, red

HERE = Path(__file__).resolve().parent


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "traces" / "latest.jsonl"
    records = load_jsonl(path)
    print(bold(f"{len(records)} spans from {path.name}"))

    print("\n" + bold("Per-claim metrics"))
    cols = ["claim", "decision", "latency_ms", "model_calls", "tool_spans", "errors", "tokens"]
    print("  ".join(c.ljust(11) for c in cols))
    for row in per_claim_metrics(records):
        print("  ".join(str(row[c]).ljust(11) for c in cols))

    if not any(r.attr("gen_ai.operation.name") == "execute_tool" for r in records):
        print("\n" + red("No execute_tool spans in this file.") +
              " Finish Task 1, then run `python3 main.py` again.")
        return

    print("\n" + bold("Repeated payments"))
    try:
        findings = find_repeated_payments(records)
    except NotImplementedError as exc:
        print(dim(str(exc)))
        return
    if not findings:
        print("none found")
    for f in findings:
        print(red(f"{f.claim_id}: approve_payment ran {f.attempts} times") +
              f"  call ids {', '.join(f.call_ids)}  ->  {f.cause}")


if __name__ == "__main__":
    main()
