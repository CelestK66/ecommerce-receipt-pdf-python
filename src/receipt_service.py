from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class Checkout:
    order_id: str
    customer_email: str
    total_cents: int
    items: tuple[str, ...]
    payment_status: str


@dataclass(frozen=True)
class Fulfillment:
    order_id: str
    status: str


class ReceiptDecision(str, Enum):
    ISSUED = "issued"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReceiptResult:
    decision: ReceiptDecision
    order_id: str
    pdf: dict | None = None
    message_id: str | None = None


def issue_receipt(checkout: Checkout, fulfillment: Fulfillment, client: InfraiClient) -> ReceiptResult:
    if checkout.payment_status != "paid" or fulfillment.order_id != checkout.order_id or fulfillment.status != "fulfilled":
        return ReceiptResult(ReceiptDecision.REJECTED, checkout.order_id)
    lines = "\n".join(f"- {item}" for item in checkout.items)
    markdown = f"# Receipt {checkout.order_id}\n\n{lines}\n\nTotal: ${checkout.total_cents / 100:.2f}"
    pdf = client.generate_receipt(markdown)
    message = client.send_order_update(checkout.customer_email, f"Receipt for order {checkout.order_id}", "Your payment receipt is ready.")
    return ReceiptResult(ReceiptDecision.ISSUED, checkout.order_id, pdf, message.get("data", {}).get("message_id"))
