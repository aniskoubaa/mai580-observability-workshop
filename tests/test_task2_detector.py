"""Task 2 tests use hand-made spans, so they do not depend on Task 1."""
import unittest

from analysis import Finding, find_repeated_payments
from tests.helpers import agent_span, tool_span


class TestTask2Detector(unittest.TestCase):
    def test_one_payment_is_fine(self):
        records = [agent_span("t1", "C-1"), tool_span("t1", "0002", "approve_payment", "call_a")]
        self.assertEqual(find_repeated_payments(records), [])

    def test_harness_retry(self):
        records = [agent_span("t1", "C-1"),
                   tool_span("t1", "0002", "approve_payment", "call_a", status="ERROR"),
                   tool_span("t1", "0003", "approve_payment", "call_a")]
        self.assertEqual(find_repeated_payments(records),
                         [Finding("C-1", 2, ("call_a", "call_a"), "harness retry")])

    def test_model_asked_twice(self):
        records = [agent_span("t1", "C-1"),
                   tool_span("t1", "0002", "approve_payment", "call_a"),
                   tool_span("t1", "0003", "approve_payment", "call_b")]
        self.assertEqual(find_repeated_payments(records),
                         [Finding("C-1", 2, ("call_a", "call_b"), "model asked twice")])

    def test_other_tools_may_repeat(self):
        records = [agent_span("t1", "C-1"),
                   tool_span("t1", "0002", "read_receipt", "call_a"),
                   tool_span("t1", "0003", "read_receipt", "call_a"),
                   tool_span("t1", "0004", "approve_payment", "call_b")]
        self.assertEqual(find_repeated_payments(records), [])

    def test_payments_in_different_traces_are_not_mixed(self):
        records = [agent_span("t1", "C-1"), tool_span("t1", "0002", "approve_payment", "call_a"),
                   agent_span("t2", "C-2"), tool_span("t2", "0002", "approve_payment", "call_a")]
        self.assertEqual(find_repeated_payments(records), [])

    def test_sorted_by_claim(self):
        records = []
        for trace, claim in [("t1", "C-9"), ("t2", "C-3")]:
            records += [agent_span(trace, claim),
                        tool_span(trace, "0002", "approve_payment", "x"),
                        tool_span(trace, "0003", "approve_payment", "x")]
        self.assertEqual([f.claim_id for f in find_repeated_payments(records)], ["C-3", "C-9"])


if __name__ == "__main__":
    unittest.main()
