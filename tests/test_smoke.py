"""Passes before any task: the agent runs and writes agent and chat spans."""
import unittest

from agent import load_claims
from tests.helpers import run


class TestSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.answers, cls.gateway = run()

    def test_every_claim_gets_the_expected_decision(self):
        for claim in load_claims():
            self.assertTrue(self.answers[claim.id].startswith(claim.expected), claim.id)

    def test_one_trace_per_claim(self):
        roots = [r for r in self.records if not r.parent_id]
        self.assertEqual(len(roots), 6)
        self.assertTrue(all(r.name == "invoke_agent trip-claim-agent" for r in roots))

    def test_chat_spans_carry_token_usage(self):
        chats = [r for r in self.records if r.name == "chat trip-claim-replay"]
        self.assertEqual(len(chats), 31)
        self.assertTrue(all(r.attr("gen_ai.usage.input_tokens", 0) > 0 for r in chats))

    def test_the_bug_is_there_on_purpose(self):
        self.assertEqual(self.gateway.payments_for("C-104"), 2)   # finance sees two payments


if __name__ == "__main__":
    unittest.main()
