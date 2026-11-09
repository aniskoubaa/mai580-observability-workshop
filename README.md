# The Agent Said "Paid Once". Finance Saw Two Payments.

A hands-on MAI580 workshop on agent observability: OpenTelemetry spans, trace
queries, privacy in traces, and LangSmith.

**Prof. Anis Koubaa · Alfaisal University · Fall 2026 · Topic 10**

A trip-claim agent approves or rejects six travel-expense claims. For claim C-104
the agent answers "1,240 SAR paid", and the answer is correct. But finance finds
**two** payments of 1,240 SAR in the bank ledger. The agent's answer cannot tell
you why. A trace can.

In this workshop you instrument the agent with OpenTelemetry, find the cause in
the trace, write a query that finds it automatically, stop the traces from
leaking bank details, and then send the same traces to LangSmith without changing
the agent's code.

## Start here

You need Python 3.10 or later. No API key is needed for Tasks 0–3: the model's
answers are scripted, so everyone sees the same traces.

```bash
git clone https://github.com/aniskoubaa/mai580-observability-workshop.git
cd mai580-observability-workshop
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

`python3 main.py` runs the six claims, prints each trace as a tree, and compares
what the agent said with what finance sees. Then run:

```bash
python3 analyze.py                 # query the saved traces
python3 -m unittest                # the smoke tests pass; the task tests fail until you write them
```

## Words you need

| Word | Meaning in this lab |
|---|---|
| **Span** | One timed step: one model call, one tool attempt, or the whole claim. It has a name, a start and end time, a status, and attributes. |
| **Trace** | All the spans of one claim, linked into a tree by their parent span. |
| **Attribute** | A key–value fact on a span, for example `gen_ai.tool.name = "approve_payment"`. |
| **Exporter** | The part that sends finished spans somewhere: a file, the terminal, or LangSmith. |
| **OTLP** | The OpenTelemetry network protocol. LangSmith, Langfuse, Jaeger and Phoenix all accept it. |
| **GenAI semantic conventions** | The agreed names for agent spans and attributes (`invoke_agent`, `chat`, `execute_tool`, `gen_ai.*`). Status: Development, so names can still change. |

## The agent

```
claim ──> TripClaimAgent ──> model (scripted)  "call these tools"
                │
                └──> ToolRunner ──> get_policy, read_receipt, convert_currency,
                     (the harness)   check_budget, approve_payment, send_email
```

Each claim becomes one trace:

```
invoke_agent trip-claim-agent            the whole claim (root span)
├─ chat trip-claim-replay                one model call, with token usage
├─ execute_tool read_receipt             one tool attempt          <- Task 1
├─ chat trip-claim-replay
└─ ...
```

## Where each idea lives

| Folder | What it holds | Start reading at |
|---|---|---|
| `agent/` | The agent loop, the harness that runs tools, the scripted model | `agent.py`, then `tool_runner.py` |
| `tools/` | The six tools and a fake bank with a ledger | `registry.py`, `payment_gateway.py` |
| `tracing/` | Spans, content capture, exporters, the tree printer | `spans.py`, `setup.py` |
| `analysis/` | Queries over saved spans | `metrics.py` |
| `tests/` | One test file per task | `test_smoke.py` |

You do not need to read `agent/replay_model.py` or `tracing/tree_view.py`. They are
plumbing, and each one says so at the top.

## Your tasks

Each task is one function with a `TODO` and one test file that tells you when you are done.
Run tests **from the repository root**.

| # | File | What to write | Check |
|---|---|---|---|
| 0 | none | Run the agent. Find where C-104's second payment came from, using only what you can see. | — |
| 1 | `tracing/spans.py` | `Spans.tool()`: one `execute_tool` span per tool attempt | `python3 -m unittest tests.test_task1_tool_span` |
| 2 | `analysis/repeated_payments.py` | A query that finds every claim paid more than once, and says whether the harness or the model caused it | `python3 -m unittest tests.test_task2_detector` |
| 3 | `tracing/content.py` | Respect `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` and redact IBANs | `python3 -m unittest tests.test_task3_privacy` |
| 4 | `.env` | Send the same traces to LangSmith over OTLP. No code change. | See below |

Follow [WORKSHOP.md](WORKSHOP.md) for the steps and the questions. Record your
evidence in [TEAM_REPORT.md](TEAM_REPORT.md).

## Task 4: LangSmith in two lines

LangSmith accepts OpenTelemetry traces directly. You do not need the `langsmith`
package: the OTLP exporter you already installed is enough.

1. Create a free account at [smith.langchain.com](https://smith.langchain.com) and
   create an API key in Settings.
2. Copy the settings file and paste your key:

   ```bash
   cp .env.example .env               # Windows: copy .env.example .env
   ```

   ```
   OTEL_EXPORTER_OTLP_ENDPOINT=https://api.smith.langchain.com/otel
   OTEL_EXPORTER_OTLP_HEADERS=x-api-key=<your key>,Langsmith-Project=mai580-observability-lab
   ```

3. Run with the OTLP exporter switched on:

   ```bash
   python3 main.py --otlp --capture SPAN_ONLY
   ```

4. Open the project `mai580-observability-lab` in LangSmith. You should see six runs
   named `invoke_agent trip-claim-agent`.

Write the endpoint **without** `/v1/traces`: the exporter adds it. EU accounts use
`https://eu.api.smith.langchain.com/otel`. If your workspace uses agents instead of
projects, LangSmith's
[OpenTelemetry guide](https://docs.langchain.com/langsmith/trace-with-opentelemetry)
lists the headers to use instead of `Langsmith-Project`.

`.env` is in `.gitignore`. Never commit your key.

**Same traces, other backends.** Change the two lines in `.env` to send the same
spans to Langfuse, Jaeger or Arize Phoenix. The agent code does not change. That is
the point of OpenTelemetry: the instrumentation is written once and the backend is
replaceable.

## What is real and what is simulated

- **Real:** the OpenTelemetry SDK, the span names and attributes (OTel GenAI
  conventions, checked November 2026), the OTLP export, LangSmith ingestion.
- **Simulated:** the model (a script in `data/recorded_run.json`; it does not read
  tool results), the bank, and the six claims. Names, amounts and IBANs are invented.
- **Content capture:** the Python GenAI instrumentations use the variable
  `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` with the values `NO_CONTENT`
  (default), `SPAN_ONLY`, `EVENT_ONLY` and `SPAN_AND_EVENT`. This lab writes span
  attributes only, so content appears only with `SPAN_ONLY` or `SPAN_AND_EVENT`.
- **LangSmith mapping:** LangSmith reads `gen_ai.input.messages`, `gen_ai.usage.*`,
  `gen_ai.tool.name` and `gen_ai.request.model`. It did not map
  `gen_ai.tool.call.arguments` and `gen_ai.tool.call.result` when this lab was written,
  so tool spans also carry `input.value` and `output.value`, which LangSmith shows as
  the run's input and output. The root span carries `langsmith.span.kind = "chain"`.
  These are the only LangSmith-specific lines in the code.

## Files

| File | Purpose |
|---|---|
| `main.py` | Runs the claims, writes `traces/latest.jsonl`, prints trees and the ledger check |
| `analyze.py` | Reads saved traces: per-claim metrics and the Task 2 detector |
| `data/claims.json` | Six fictional claims and the decision a careful human would make |
| `data/receipts.json` | Fictional receipts; each carries an IBAN |
| `data/recorded_run.json` | The scripted model turns |
| `WORKSHOP.md` | Steps, questions, and stretch tasks |
| `TEAM_REPORT.md` | Evidence template |

Adapted from the [MAI580 course repository](https://github.com/aniskoubaa/mai580_agentic_ai),
Topic 10. Code is MIT licensed; teaching materials are CC BY-NC-SA 4.0.
See [LICENSE](LICENSE).
