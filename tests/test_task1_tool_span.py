import unittest

from tests.helpers import run


class TestTask1ToolSpan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, _, _ = run(["C-103", "C-104"], capture="SPAN_ONLY")
        cls.tools = [r for r in cls.records if r.name.startswith("execute_tool")]

    def setUp(self):
        if not self.tools:
            self.fail("TASK 1: no execute_tool spans yet. Write Spans.tool() in tracing/spans.py")

    def named(self, tool):
        return sorted((r for r in self.tools if r.attr("gen_ai.tool.name") == tool), key=lambda r: r.start_ns)

    def test_span_name_and_attributes(self):
        span = self.named("convert_currency")[0]
        self.assertEqual(span.name, "execute_tool convert_currency")
        self.assertEqual(span.attr("gen_ai.operation.name"), "execute_tool")
        self.assertEqual(span.attr("gen_ai.tool.call.id"), "call_104_c")
        self.assertEqual(span.attr("gen_ai.tool.type"), "function")

    def test_tool_span_is_a_child_of_the_agent_span(self):
        span = self.named("convert_currency")[0]
        parent = next(r for r in self.records if r.span_id == span.parent_id)
        self.assertEqual(parent.attr("gen_ai.operation.name"), "invoke_agent")

    def test_arguments_are_recorded_when_capture_is_on(self):
        span = self.named("convert_currency")[0]
        self.assertIn("EGP", span.attr("gen_ai.tool.call.arguments", ""),
                      "add the attributes from self.tool_arguments(call)")

    def test_timeout_is_an_error_span(self):
        first, second = self.named("approve_payment")
        self.assertEqual(first.status, "ERROR")
        self.assertEqual(first.attr("error.type"), "TimeoutError")
        self.assertNotEqual(second.status, "ERROR")

    def test_both_attempts_share_one_call_id(self):
        ids = {r.attr("gen_ai.tool.call.id") for r in self.named("approve_payment")}
        self.assertEqual(ids, {"call_104_e"})

    def test_missing_receipt_is_an_error_span(self):
        span = self.named("read_receipt")[0]      # C-103 has no receipt
        self.assertEqual(span.status, "ERROR")
        self.assertEqual(span.attr("error.type"), "FileNotFoundError")


if __name__ == "__main__":
    unittest.main()
