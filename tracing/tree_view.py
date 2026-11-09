"""PLUMBING — prints traces as trees in the terminal. A tiny LangSmith for your console."""
import sys

COLOR = sys.stdout.isatty()


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if COLOR else text


def red(t): return _c("31;1", t)
def dim(t): return _c("2", t)
def bold(t): return _c("1", t)
def green(t): return _c("32", t)


def print_traces(records):
    by_trace = {}
    for r in records:
        by_trace.setdefault(r.trace_id, []).append(r)
    for spans in sorted(by_trace.values(), key=lambda s: min(x.start_ns for x in s)):
        root = next((s for s in spans if not s.parent_id), spans[0])
        claim = root.attr("app.claim.id", "?")
        print()
        print(bold(f"{claim}") + dim(f"  trace {root.trace_id[:12]}…  {len(spans)} spans"))
        _print(root, spans, prefix="", last=True)


def _print(span, spans, prefix, last):
    branch = "└─ " if last else "├─ "
    print(f"{prefix}{branch}{_label(span)}")
    children = sorted((s for s in spans if s.parent_id == span.span_id), key=lambda s: s.start_ns)
    for i, child in enumerate(children):
        _print(child, spans, prefix + ("   " if last else "│  "), i == len(children) - 1)


def _label(s):
    name = s.name.ljust(34)
    ms = f"{s.duration_ms:7.0f} ms"
    notes = []
    if s.attr("gen_ai.operation.name") == "chat":
        notes.append(f"in {s.attr('gen_ai.usage.input_tokens', 0)} / out {s.attr('gen_ai.usage.output_tokens', 0)} tok")
    if s.attr("gen_ai.tool.call.id"):
        notes.append(f"call {s.attr('gen_ai.tool.call.id')}")
    if s.attr("app.claim.decision"):
        notes.append(s.attr("app.claim.decision"))
    text = f"{name} {dim(ms)}  {dim('  '.join(notes))}"
    if s.status == "ERROR":
        text += "  " + red(f"ERROR {s.attr('error.type', '')}")
    return text
