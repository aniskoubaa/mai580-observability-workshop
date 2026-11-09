"""PLUMBING — you do not need to read this for the tasks.

A stand-in for an LLM. It replays hand-written turns from data/recorded_run.json,
so the lab needs no API key and every student sees the same traces.

Token counts are estimated as (characters / 4), so they grow as the conversation
grows, which is what you would see with a real model.
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass
class ToolCall:
    id: str            # the model's id for this request; becomes gen_ai.tool.call.id
    name: str
    arguments: dict


@dataclass
class ModelReply:
    tool_calls: list = field(default_factory=list)
    final: str = None
    input_tokens: int = 0
    output_tokens: int = 0

    def as_message(self) -> dict:
        if self.final is not None:
            return {"role": "assistant", "content": self.final}
        return {"role": "assistant",
                "tool_calls": [{"id": c.id, "name": c.name, "arguments": c.arguments} for c in self.tool_calls]}


class ReplayModel:
    provider = "replay"

    def __init__(self, path=DATA / "recorded_run.json"):
        recording = json.loads(Path(path).read_text(encoding="utf-8"))
        self.name = recording["model"]
        self._turns = recording["claims"]

    def reply(self, claim_id: str, step: int, messages: list) -> ModelReply:
        time.sleep(0.05)   # a real model call takes time
        turns = self._turns.get(claim_id)
        if turns is None or step >= len(turns):
            raise RuntimeError(f"The recording has no turn {step} for claim {claim_id}.")
        turn = turns[step]
        reply = ModelReply(
            tool_calls=[ToolCall(c["id"], c["name"], c["arguments"]) for c in turn.get("tool_calls", [])],
            final=turn.get("final"),
        )
        reply.input_tokens = len(json.dumps(messages)) // 4
        reply.output_tokens = len(json.dumps(reply.as_message())) // 4
        return reply
