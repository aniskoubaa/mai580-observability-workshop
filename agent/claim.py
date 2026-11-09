"""One trip-expense claim, and the code that loads them from data/claims.json."""
import json
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Claim:
    id: str
    employee: str
    email: str
    dept: str
    trip: str
    receipt: str
    expected: str            # what a careful human would decide: APPROVE or REJECT
    expected_payments: int   # how many rows finance should see in the ledger

    def as_request(self) -> str:
        return (f"Claim {self.id} from {self.employee} ({self.email}), {self.dept} department. "
                f"Trip: {self.trip}. Receipt file: {self.receipt}.")


def load_claims(ids=None) -> list:
    raw = json.loads((DATA / "claims.json").read_text(encoding="utf-8"))["claims"]
    claims = [Claim(**c) for c in raw]
    if ids:
        unknown = set(ids) - {c.id for c in claims}
        if unknown:
            raise SystemExit(f"Unknown claim id(s): {', '.join(sorted(unknown))}. "
                             f"Choose from {', '.join(c.id for c in claims)}.")
        claims = [c for c in claims if c.id in ids]
    return claims
