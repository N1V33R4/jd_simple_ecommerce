from django import template
from cart.utils import get_or_set_order_session

register = template.Library()

@register.filter
def cart_item_count(request) -> int:
  order = get_or_set_order_session(request)
  count = order.items.count() # type: ignore
  return count
