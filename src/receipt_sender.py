from __future__ import annotations

import json
import argparse
import os

from .infrai_client import InfraiClient
from .receipt_service import Checkout, Fulfillment, issue_receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue a receipt after storefront fulfillment")
    parser.add_argument(
        "--recipient",
        default=os.environ.get("RECEIPT_RECIPIENT"),
        help="recipient email address (or set RECEIPT_RECIPIENT)",
    )
    args = parser.parse_args()
    if not args.recipient:
        parser.error("--recipient or RECEIPT_RECIPIENT is required")

    checkout = Checkout("order-1042", args.recipient, 4899, ("Canvas tote", "Shipping"), "paid")
    fulfillment = Fulfillment("order-1042", "fulfilled")
    result = issue_receipt(checkout, fulfillment, InfraiClient())
    print(json.dumps({"decision": result.decision.value, "order_id": result.order_id, "message_id": result.message_id}, indent=2))


if __name__ == "__main__":
    main()
