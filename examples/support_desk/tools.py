"""
Plain Python tools for the Support Desk example.

Deterministic, no network — a fake orders database and a refund policy the
specialist agents can consult.
"""

import json

# Fake orders database keyed by order id.
_ORDERS = {
    "A1001": {"item": "Wireless Headphones", "status": "shipped", "eta": "2 days", "total": 129.00},
    "A1002": {"item": "Mechanical Keyboard", "status": "processing", "eta": "5 days", "total": 89.00},
    "A1003": {"item": "USB-C Cable", "status": "delivered", "eta": "-", "total": 12.00},
}


def lookup_order(order_id: str) -> str:
    """
    Look up an order's status, item, ETA, and total by its id.

    :param order_id: The order identifier, e.g. "A1001".
    :return: A JSON string with the order details, or a not-found message.
    """
    order = _ORDERS.get(order_id.strip().upper())
    if not order:
        return f"No order found with id '{order_id}'."
    return json.dumps({"order_id": order_id.strip().upper(), **order})


def refund_policy() -> str:
    """
    Return the store's refund policy.

    :return: The refund policy text.
    """
    return (
        "Refunds are available within 30 days of delivery for unused items. "
        "Refunds are processed to the original payment method within 5–7 business days. "
        "Shipped-but-undelivered orders must be received back before a refund is issued."
    )
