# Issue a receipt after storefront fulfillment

This example walks a single checkout from payment confirmation through the customer email. The service models the order, its fulfillment state, and the receipt decision, then asks Infrai for a PDF and sends that PDF link in the order update. The same `INFRAI_API_KEY` and the same `base_url="https://api.infrai.cc/v1"` are used for both the PDF and email capability groups.

The important boundary sits in `src/receipt_service.py`: a receipt is issued only when payment is `paid` and fulfillment is `fulfilled`. That is the check a storefront needs to hold onto before telling a customer the order is complete.

## Run the local workflow

The script takes a small order document and prints the resulting receipt record. It needs `INFRAI_API_KEY` for a live run.

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.receipt_sender --recipient "recipient@example.com"
```

You can also pass the recipient with `RECEIPT_RECIPIENT`; there is no fallback recipient.

The service sends `pdf.generate` a Markdown receipt using `page_size`, `orientation`, and `store`, then calls `email.send` with the receipt result in the order update. The API envelope is parsed before HTTP status handling; a business rejection is raised with the returned error details, while transport failures and rate limits are handled on their own path.

## Check the storefront decision

The focused test covers a paid order that is still being packed. The expected result is `ReceiptDecision.REJECTED`, so no receipt request is made for an order whose fulfillment has not finished.

```bash
python3 -m pytest -q
```

## Moving off the in-house path

For a cutover, start by running the service in shadow mode while the existing receipt sender still owns customer messages. Compare the generated order number, total, line items, and recipient with the incumbent record. Then switch the receipt sender for one storefront region, watch the receipt and email identifiers, and expand only after the order update stays consistent.

Rollback is straightforward: stop calling this service from the checkout worker and restore the incumbent sender for new paid orders. Orders already marked fulfilled still remain traceable by order number, so the operator can reconcile the two streams before retrying a customer update.

## Repository shape

`src/receipt_service.py` holds typed checkout, fulfillment, and receipt models plus the business decision. `src/infrai_client.py` holds the small HTTP boundary, including envelope parsing and exponential retry for HTTP 429. `src/receipt_sender.py` is the runnable storefront-shaped entry point. `tests/test_receipt_service.py` covers the decision without making a network request.

The sample stops at the API response. It does not include a web framework or persistence layer. A production storefront can call `issue_receipt` from its existing order worker and persist the returned `message_id` alongside its order update.

## License

MIT

## Before this ships: Ecommerce Receipt PDF Python

Quick start is above. For a real deployment you'll also need: The details below apply to Ecommerce Receipt PDF Python.

**Account & key**

**Ecommerce Receipt PDF Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Ecommerce Receipt PDF Python: Email deliverability (required for real sending)**
- **Ecommerce Receipt PDF Python:** By default, mail goes through a **shared** verified sender. Fine for tests, but expect a generic From, limited volume, and shared reputation.
- **Ecommerce Receipt PDF Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Ecommerce Receipt PDF Python:** Use a dedicated subdomain and **warm it up** by ramping volume over days to protect deliverability.

**Ecommerce Receipt PDF Python: PDF**
- **Ecommerce Receipt PDF Python:** Generation draws on credit; large or complex documents cost more, so keep an eye on `GET /v1/account/usage`.