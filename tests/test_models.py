# pyright: standard
from target_orders import parse_orders_from_html
from target_orders.models import Order


def test_parse_orders_from_html(sample_html):
    """Test parsing orders from HTML."""
    orders = parse_orders_from_html(sample_html)
    assert len(orders) > 0, "No orders found in the HTML"
    assert all(isinstance(order, Order) for order in orders), (
        "Not all parsed items are of type Order"
    )
