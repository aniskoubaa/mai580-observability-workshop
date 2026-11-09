"""A fake bank. It keeps a ledger: one row per payment that actually left the company.

The gateway is slow for one claim. It records the payment first and only then
fails to answer in time. Real payment APIs behave like this: a timeout tells you
that you did not hear back, not that nothing happened.
"""
import time


class PaymentGateway:
    TIMEOUT_S = 0.3

    def __init__(self, slow_claims=("C-104",)):
        self.ledger = []                 # what finance sees at the end of the day
        self._slow = set(slow_claims)
        self._already_slow = set()

    def approve_payment(self, claim_id: str, amount_sar: float) -> dict:
        self.ledger.append({"claim_id": claim_id, "amount_sar": amount_sar})   # money is gone
        if claim_id in self._slow and claim_id not in self._already_slow:
            self._already_slow.add(claim_id)
            time.sleep(self.TIMEOUT_S)
            raise TimeoutError(f"payment gateway did not answer within {self.TIMEOUT_S} s")
        time.sleep(0.04)
        return {"status": "paid", "payment_id": f"PAY-{len(self.ledger):04d}", "amount_sar": amount_sar}

    def payments_for(self, claim_id: str) -> int:
        return sum(1 for row in self.ledger if row["claim_id"] == claim_id)
