# Workshop: Find the Second Payment

**Central question:** the agent's answer is correct, but the company paid twice.
What must you record about each run so that you can explain this, and catch the
next one automatically?

Work in pairs. One person types, and the other writes predictions in
`TEAM_REPORT.md` **before** each run. Swap after each task.

## Before the code · Search, brainstorm, discuss (20 min)

Do not open the lab code yet. Your instructor gives your pair one question.

1. Q1. What is observability for an LLM agent? How is it different from writing log lines?
2. Q2. What is OpenTelemetry, and what are its GenAI semantic conventions? Are they stable yet?
3. Q3. What does LangSmith do? Name two alternatives and one real difference between them.
4. Q4. Find a real case where an AI agent took a wrong action. What would a trace have shown?
5. Q5. What is an idempotency key? Why do payment APIs ask for one?
6. Q6. What personal data can end up in LLM traces? What do tracing tools offer to protect it?

**Search (8 min).** Bring back one finding in this format:

```
Claim:  one sentence
Source: the site or document
Date:   when it was published or updated
Type:   official spec / official docs / paper / vendor page / blog
```

Prefer the primary source: the specification, the official documentation, or the
paper. A vendor page tells you what the vendor sells. An AI chatbot is not a
source: follow its link and cite the page. If you cannot name the source and its
date, the claim does not go on the board.

**Brainstorm (6 min).** Each pair reads its claim aloud. The instructor writes it in
one of four columns: what to record, tools, failures, privacy and cost.

**Discuss (6 min).** Which claims come from a primary source? Where do two pairs
disagree, and how would you check? Keep your finding: you will test it on a real
trace during the lab, and your report asks about it.

## Task 0 · Look without instruments (15 min)

```bash
python3 main.py
```

1. Read the last table. Which claim does finance disagree with?
2. Look at the C-104 tree. The root span lasts about 750 ms, but its chat spans
   add up to about 300 ms. Where did the rest of the time go?
3. Open `agent/tool_runner.py` and `tools/payment_gateway.py`. Write down your
   explanation of the second payment. Mark it as a **hypothesis**: nothing you have
   seen so far proves it.
4. Run `grep -c "IBAN SA" traces/latest.jsonl` (Windows PowerShell:
   `(Select-String "IBAN SA" traces\latest.jsonl).Count`). The run said
   `content capture: NO_CONTENT`. Why is there a bank number in the file?

## Task 1 · Make tool calls visible (15 min)

Open `tracing/spans.py`. Read `agent()`, then write `tool()` as the comment at the
top of the file describes.

```bash
python3 -m unittest tests.test_task1_tool_span
python3 main.py --claim C-104
```

Now confirm or reject your Task 0 hypothesis **from the trace**:

- How many `execute_tool approve_payment` spans does C-104 have? What are their statuses?
- Compare their `gen_ai.tool.call.id`. Did the model ask twice, or did someone else repeat the call?
- The model's next chat span says "paid". Did the model ever learn about the timeout?

## Task 2 · Query the traces (15 min)

You found one double payment by eye. A real system runs thousands of claims a day.
Open `analysis/repeated_payments.py` and write `find_repeated_payments`.

```bash
python3 -m unittest tests.test_task2_detector
python3 analyze.py
```

Questions:

- Your detector reports "harness retry". Name a fix for that cause, and a different
  fix for "model asked twice".
- Is a retry ever safe for `approve_payment`? What would the payment API need to
  offer? (Hint: search for "idempotency key".)
- Look at the metrics table. Which number would you put on an alert, and at what threshold?

## Task 3 · Stop the leak (10 min)

Open `tracing/content.py` and write `redact` and `capture`.

```bash
python3 -m unittest tests.test_task3_privacy
python3 main.py --quiet && grep -c "IBAN SA" traces/latest.jsonl        # expect 0
python3 main.py --quiet --capture SPAN_ONLY && grep -c "REDACTED" traces/latest.jsonl
```

Questions:

- The default is `NO_CONTENT`. What can you still debug with no content at all?
  What can you no longer debug?
- Your redaction removes IBANs. List two other kinds of personal data these traces
  still carry. Where else do they appear?

## Task 4 · Same traces, in LangSmith (15 min)

Follow "Task 4: LangSmith in two lines" in the README, then:

```bash
python3 main.py --otlp --capture SPAN_ONLY
```

In LangSmith, open the run for C-104.

- Find the failed `approve_payment` attempt. How does LangSmith show the error?
- Open a chat run. Where does LangSmith show the token counts? Which attribute fed them?
- Open a tool run. Is the IBAN visible? Why or why not?
- Run once more with `--capture NO_CONTENT`. What disappears from LangSmith, and what stays?
- Which lines of code would change if your company moved from LangSmith to Langfuse?

## Stretch tasks

1. **Fix the bug.** Make `approve_payment` idempotent in `tools/payment_gateway.py`:
   at most one payment per claim. Run `main.py` again. The trace still shows two
   attempts, but finance now sees one payment. `test_the_bug_is_there_on_purpose`
   will fail, which is the point.
2. **Mark retries.** In `ToolRunner.run`, put the attempt number on the tool span
   (for example `app.tool.attempt`). Which question does this answer faster?
3. **Your own agent.** Lab 4 asks you to instrument your project agent. Copy
   `tracing/` into your project and wrap your model calls and tool calls with the
   same three span types.

## Deliverables

- Your three tasks passing: `python3 -m unittest` shows `OK`.
- A completed [TEAM_REPORT.md](TEAM_REPORT.md).
- One screenshot from LangSmith of the C-104 trace, with the failed attempt visible.
