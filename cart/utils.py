from .models import Order

def get_or_set_order_session(request) -> Order:
  """
  Get order associated with session.  
  Create new if has no order or order was deleted.  
  
  If user is logged in, set user to that order. 
  """
  order_id = request.session.get('order_id', None)
  if order_id is None:
    order = Order()
    order.save() 
    request.session['order_id'] = order.id # type: ignore
  else:
    try:
      order = Order.objects.get(id=order_id, ordered=False)
    except Order.DoesNotExist:
      order = Order()
      order.save() 
      request.session['order_id'] = order.id # type: ignore
  
  if request.user.is_authenticated and order.user is None:
    order.user = request.user
    order.save()
  
  return order
