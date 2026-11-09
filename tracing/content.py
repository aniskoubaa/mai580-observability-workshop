"""TASK 3 — stop leaking personal data into your traces.

Prompts, tool arguments and tool results are "content". Every receipt in this
lab carries the employee's bank IBAN, so content is personal data. The OTel GenAI
conventions make content Opt-In, and the Python GenAI instrumentations read one
environment variable to decide where it may go:

    OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT
        NO_CONTENT      (default)  never record content
        SPAN_ONLY                  record content as span attributes
        EVENT_ONLY                 record content as events, not on spans
        SPAN_AND_EVENT             both

This lab only writes span attributes, so content goes on spans only for
SPAN_ONLY and SPAN_AND_EVENT.

The starter code below captures everything, always, and never redacts.
Run `python3 main.py` and then `grep -c "IBAN SA" traces/latest.jsonl` to see the leak.

Write two methods:

    redact(text)          replace every IBAN with "[REDACTED-IBAN]"
                          (use IBAN_PATTERN, it is already written for you)

    capture(name, value)  NO_CONTENT or EVENT_ONLY  ->  {}
                          SPAN_ONLY or SPAN_AND_EVENT ->  {name: redacted text}
                          A value that is not a string is first turned into text
                          with json.dumps(value, ensure_ascii=False).

Check your work:  python3 -m unittest tests.test_task3_privacy
"""
import json
import os
import re

ENV_VAR = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"
MODES = ("NO_CONTENT", "SPAN_ONLY", "EVENT_ONLY", "SPAN_AND_EVENT")

# Two letters, two check digits, then 11 to 30 letters or digits in groups of four,
# with or without spaces. Matches SA44 2000 0001 2345 6789 1234 and SA4420000001234567891234.
IBAN_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b")
REDACTED = "[REDACTED-IBAN]"


class ContentPolicy:
    def __init__(self, mode: str = None):
        mode = (mode or os.environ.get(ENV_VAR) or "NO_CONTENT").strip().upper()
        if mode not in MODES:
            raise ValueError(f"{ENV_VAR}={mode!r} is not one of {', '.join(MODES)}")
        self.mode = mode

    def on_spans(self) -> bool:
        """True when this mode allows content as span attributes."""
        return self.mode in ("SPAN_ONLY", "SPAN_AND_EVENT")

    def redact(self, text: str) -> str:
        # TODO (Task 3): replace every IBAN in text with REDACTED.
        return text

    def capture(self, name: str, value) -> dict:
        # TODO (Task 3): respect self.mode, and redact what you keep.
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return {name: text}
