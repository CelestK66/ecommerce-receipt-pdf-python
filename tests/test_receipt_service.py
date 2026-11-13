from unittest.mock import Mock

from src.receipt_service import Checkout, Fulfillment, ReceiptDecision, issue_receipt


def test_paid_order_waits_for_fulfillment_before_receipt() -> None:
    checkout = Checkout("order-7", "buyer@example.com", 1200, ("Notebook",), "paid")
    client = Mock()
    result = issue_receipt(checkout, Fulfillment("order-7", "packing"), client)
    assert result.decision is ReceiptDecision.REJECTED
    client.generate_receipt.assert_not_called()
    client.send_order_update.assert_not_called()
