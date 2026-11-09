"""The six tools of the trip-claim agent (Topic 10 running example).

Each tool sleeps a few milliseconds so that span durations look like real calls.
"""
import json
import time
from pathlib import Path

from tools.payment_gateway import PaymentGateway
from tools.tool import Tool

DATA = Path(__file__).resolve().parent.parent / "data"

POLICY = {
    "hotel": "Hotels: up to 1,000 SAR per claim. An itemised receipt is required.",
    "conference": "Conference fees are covered in full with a receipt.",
    "training": "Training fees are covered in full with a receipt and manager approval on file.",
    "receipts": "Every claim needs a receipt. No receipt, no payment.",
}
RATES_TO_SAR = {"SAR": 1.0, "USD": 3.75, "EGP": 0.0775, "AED": 1.02}
BUDGET_LEFT_SAR = {"Engineering": 5000, "Research": 3000, "Sales": 2000, "Marketing": 1200}


def build_tools(gateway: PaymentGateway) -> dict:
    receipts = json.loads((DATA / "receipts.json").read_text(encoding="utf-8"))

    def get_policy(section: str) -> dict:
        time.sleep(0.01)
        return {"section": section, "text": POLICY.get(section, "No such policy section.")}

    def read_receipt(receipt: str) -> dict:
        time.sleep(0.03)
        if receipt not in receipts:
            raise FileNotFoundError(f"receipt {receipt} was not uploaded")
        return receipts[receipt]

    def convert_currency(amount: float, from_currency: str, to_currency: str = "SAR") -> dict:
        time.sleep(0.02)
        rate = RATES_TO_SAR[from_currency] / RATES_TO_SAR[to_currency]
        return {"amount": round(amount * rate, 2), "currency": to_currency, "rate": rate}

    def check_budget(dept: str, amount_sar: float) -> dict:
        time.sleep(0.01)
        left = BUDGET_LEFT_SAR.get(dept, 0)
        return {"dept": dept, "left_sar": left, "enough": amount_sar <= left}

    def send_email(to: str, body: str) -> dict:
        time.sleep(0.02)
        return {"sent": True, "to": to}

    tools = [
        Tool("get_policy", "Read one section of the travel policy.", get_policy, "datastore"),
        Tool("read_receipt", "Read an uploaded receipt.", read_receipt, "datastore"),
        Tool("convert_currency", "Convert an amount to another currency.", convert_currency),
        Tool("check_budget", "Check the department's remaining travel budget.", check_budget),
        Tool("approve_payment", "Pay the employee. Money leaves the company.", gateway.approve_payment),
        Tool("send_email", "Email the employee.", send_email),
    ]
    return {t.name: t for t in tools}
