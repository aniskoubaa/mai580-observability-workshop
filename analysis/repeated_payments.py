"""TASK 2 — find every claim that was paid more than once, from the traces alone.

You found one double payment by eye in Task 0. A real system runs thousands of
claims a day, so nobody reads every trace. Write a query that finds them.

Input:  a list of SpanRecord (see tracing/records.py) from one or more traces.
Output: one Finding per claim whose trace holds MORE THAN ONE approve_payment
        tool span. Sort the findings by claim_id.

    claim_id   take it from the agent span of the same trace: the span whose
               gen_ai.operation.name is "invoke_agent" has app.claim.id
    attempts   how many approve_payment spans that trace holds
    call_ids   the gen_ai.tool.call.id of each of those spans, in start order
    cause      "harness retry"     if all call_ids are the same
               "model asked twice" if they differ

Why the cause matters: one call id means the model asked once and the harness
repeated it. Two call ids mean the model itself asked twice. Each has a
different fix.

A tool span for approve_payment has gen_ai.tool.name == "approve_payment".

Check your work:  python3 -m unittest tests.test_task2_detector
Then run it on your traces:  python3 analyze.py
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    claim_id: str
    attempts: int
    call_ids: tuple
    cause: str


def find_repeated_payments(records: list) -> list:
    # TODO (Task 2)
    raise NotImplementedError("TASK 2: write find_repeated_payments in analysis/repeated_payments.py")
