"""The trip-claim agent: ask the model, run the tools it asks for, repeat.

Every step is wrapped in a span, so one claim produces one trace:

    invoke_agent trip-claim-agent          (one per claim: the root span)
    ├── chat trip-claim-replay             (one per model call)
    ├── execute_tool read_receipt          (one per tool attempt — Task 1)
    └── ...
"""
import json

from agent.claim import Claim

SYSTEM = ("You process trip-expense claims. Read the receipt and the policy, convert to SAR, "
          "check the budget, then approve and pay, or reject. Always email the employee.")


class TripClaimAgent:
    name = "trip-claim-agent"
    MAX_STEPS = 8

    def __init__(self, model, runner, spans):
        self.model = model
        self.runner = runner
        self.spans = spans

    def run(self, claim: Claim) -> str:
        with self.spans.agent(self.name, claim.id) as agent_span:
            messages = [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": claim.as_request()}]
            for step in range(self.MAX_STEPS):
                with self.spans.chat(self.model, messages) as chat_span:
                    reply = self.model.reply(claim.id, step, messages)
                    self.spans.chat_result(chat_span, reply)
                messages.append(reply.as_message())

                if reply.final is not None:
                    self.spans.agent_result(agent_span, reply.final)
                    return reply.final

                for call in reply.tool_calls:
                    result = self.runner.run(call)
                    messages.append({"role": "tool", "tool_call_id": call.id,
                                     "content": json.dumps(result, ensure_ascii=False)})
            return "STOPPED: too many steps"
