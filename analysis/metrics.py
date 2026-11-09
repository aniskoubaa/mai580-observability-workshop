"""Per-claim numbers computed from spans: the same table a tracing dashboard shows."""


def per_claim_metrics(records: list) -> list:
    by_trace = {}
    for r in records:
        by_trace.setdefault(r.trace_id, []).append(r)

    rows = []
    for spans in by_trace.values():
        root = next((s for s in spans if s.attr("gen_ai.operation.name") == "invoke_agent"), None)
        if root is None:
            continue
        chats = [s for s in spans if s.attr("gen_ai.operation.name") == "chat"]
        tools = [s for s in spans if s.attr("gen_ai.operation.name") == "execute_tool"]
        rows.append({
            "claim": root.attr("app.claim.id"),
            "decision": root.attr("app.claim.decision", "?"),
            "latency_ms": round(root.duration_ms),
            "model_calls": len(chats),
            "tool_spans": len(tools),
            "errors": sum(1 for s in spans if s.status == "ERROR"),
            "tokens": sum(s.attr("gen_ai.usage.input_tokens", 0) + s.attr("gen_ai.usage.output_tokens", 0)
                          for s in chats),
        })
    return sorted(rows, key=lambda r: r["claim"])
