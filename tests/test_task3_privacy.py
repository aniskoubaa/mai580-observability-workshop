import json
import unittest

from tests.helpers import run
from tracing import ContentPolicy

IBAN_SPACED = "SA44 2000 0001 2345 6789 1234"
IBAN_COMPACT = "AE070331234567890123456"


class TestTask3Redact(unittest.TestCase):
    policy = ContentPolicy("SPAN_ONLY")

    def test_spaced_iban(self):
        self.assertEqual(self.policy.redact(f"Pay to IBAN {IBAN_SPACED}."), "Pay to IBAN [REDACTED-IBAN].")

    def test_compact_iban(self):
        self.assertEqual(self.policy.redact(f"{IBAN_COMPACT} ok"), "[REDACTED-IBAN] ok")

    def test_other_text_is_kept(self):
        text = "Claim C-104: 16,000 EGP is 1,240 SAR. Call call_104_e."
        self.assertEqual(self.policy.redact(text), text)


class TestTask3Capture(unittest.TestCase):
    def test_no_content_is_the_default(self):
        self.assertEqual(ContentPolicy().capture("input.value", "hello"), {})

    def test_no_content(self):
        self.assertEqual(ContentPolicy("NO_CONTENT").capture("input.value", "hello"), {})

    def test_event_only_puts_nothing_on_spans(self):
        self.assertEqual(ContentPolicy("EVENT_ONLY").capture("input.value", "hello"), {})

    def test_span_only_keeps_redacted_text(self):
        got = ContentPolicy("SPAN_ONLY").capture("input.value", f"IBAN {IBAN_SPACED}")
        self.assertEqual(got, {"input.value": "IBAN [REDACTED-IBAN]"})

    def test_span_and_event_turns_values_into_json(self):
        got = ContentPolicy("SPAN_AND_EVENT").capture("gen_ai.tool.call.result", {"amount": 900})
        self.assertEqual(json.loads(got["gen_ai.tool.call.result"]), {"amount": 900})


class TestTask3WholeRun(unittest.TestCase):
    def test_no_iban_reaches_any_span(self):
        records, _, _ = run(["C-101"], capture="SPAN_ONLY")
        dump = json.dumps([r.attributes for r in records], ensure_ascii=False)
        self.assertIn("[REDACTED-IBAN]", dump)
        self.assertNotIn("SA44", dump)

    def test_default_run_records_no_messages(self):
        records, _, _ = run(["C-101"], capture=None)
        self.assertFalse(any("gen_ai.input.messages" in r.attributes for r in records))


if __name__ == "__main__":
    unittest.main()
