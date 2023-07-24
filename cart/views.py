from typing import Any, Dict
import json, base64, requests, datetime, stripe
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db.models import Q
from .models import Product, OrderItem, Address, Payment, Order, Category
from .utils import get_or_set_order_session
from .forms import AddToCartForm, AddressForm

stripe.api_key = 'sk_test_4eC39HqLyjWDarjtT1zdp7dc'


class ProductListView(generic.ListView):
  template_name = 'cart/product_list.html'
  queryset = Product.objects.all()

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["categories"] = Category.objects.values('name')
    return context

  def get_queryset(self):
    qs = Product.objects.all()
    category = self.request.GET.get('category', None)
    if category:
      qs = qs.filter(Q(primary_category__name=category) | Q(secondary_categories__name=category)) \
             .distinct()
    return qs


class ProductDetailView(generic.FormView):
  template_name = 'cart/product_detail.html'
  form_class = AddToCartForm
  
  def get_object(self):
    return get_object_or_404(Product, slug=self.kwargs['slug'])

  def get_success_url(self) -> str:
    return reverse('cart:summary')
  
  def get_form_kwargs(self) -> Dict[str, Any]:
    kwargs = super().get_form_kwargs()
    kwargs['product_id'] = self.get_object().id # type: ignore
    return kwargs
  
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['product'] = self.get_object()
    return context

  def form_valid(self, form: AddToCartForm) -> HttpResponse:
    order = get_or_set_order_session(self.request)
    product = self.get_object()

    item_filter = order.items.filter( # type: ignore
      product=product,
      color=form.cleaned_data['color'],
      size=form.cleaned_data['size'],
    ) 
    if item_filter.exists():
      item: OrderItem = item_filter.first()
      item.quantity += int(form.cleaned_data['quantity'])
      item.save()
    else:
      new_item: OrderItem = form.save(commit=False)
      new_item.product = product
      new_item.order = order
      new_item.save()

    return super().form_valid(form)


class CartView(generic.TemplateView):
  template_name = 'cart/cart.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['order'] = get_or_set_order_session(self.request)
    return context
  

class IncreaseQuantityView(generic.View):
  def get(self, request, *args, **kwargs):
    order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
    order_item.quantity += 1
    order_item.save()
    return redirect('cart:summary')
  

class DecreaseQuantityView(generic.View):
  def get(self, request, *args, **kwargs):
    order_item = get_object_or_404(OrderItem, id=kwargs['pk'])

    if order_item.quantity <= 1:
      order_item.delete()
    else: 
      order_item.quantity -= 1
      order_item.save()
      
    return redirect('cart:summary')
  

class RemoveFromCartView(generic.View):
  def get(self, request, *args, **kwargs):
    order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
    order_item.delete()
    return redirect('cart:summary')


class CheckoutView(generic.FormView):
  template_name = 'cart/checkout.html'
  form_class = AddressForm

  def get_form_kwargs(self) -> Dict[str, Any]:
    kwargs = super().get_form_kwargs()
    kwargs['user_id'] = self.request.user.id # type: ignore
    return kwargs
  
  def get_success_url(self) -> str:
    return reverse('cart:payment') 

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['order'] = get_or_set_order_session(self.request)
    return context

  def form_valid(self, form: Any) -> HttpResponse:
    order = get_or_set_order_session(self.request)
    selected_shipping_address = form.cleaned_data['selected_shipping_address']
    selected_billing_address = form.cleaned_data['selected_billing_address']

    if selected_shipping_address:
      order.shipping_address = selected_shipping_address
    else:
      address = Address.objects.create(
        address_type='S',
        user=self.request.user,
        address_line_1=form.cleaned_data['shipping_address_line_1'],
        address_line_2=form.cleaned_data['shipping_address_line_2'],
        zip_code=form.cleaned_data['shipping_zip_code'],
        city=form.cleaned_data['shipping_city'],
      )
      order.shipping_address = address

    if selected_billing_address:
      order.billing_address = selected_billing_address
    else:
      address = Address.objects.create(
        address_type='B',
        user=self.request.user,
        address_line_1=form.cleaned_data['billing_address_line_1'],
        address_line_2=form.cleaned_data['billing_address_line_2'],
        zip_code=form.cleaned_data['billing_zip_code'],
        city=form.cleaned_data['billing_city'],
      )
      order.billing_address = address
    order.save()

    messages.info(self.request, 'You have successfully added your addresses')
    return super().form_valid(form)


class PaymentView(generic.TemplateView):
  template_name = 'cart/payment.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['order'] = get_or_set_order_session(self.request)
    context['PAYPAL_CLIENT_ID'] = settings.PAYPAL_CLIENT_ID
    context['CALLBACK_URL'] = reverse('cart:thank-you')
    return context
  

class ThankYouView(generic.TemplateView):
  template_name = 'cart/thanks.html'


def PaypalToken():
  client_id = settings.PAYPAL_CLIENT_ID
  client_secret = settings.PAYPAL_SECRET_KEY
  url = "https://api.sandbox.paypal.com/v1/oauth2/token"
  data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type":"client_credentials"
  }
  headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
  }

  token = requests.post(url, data, headers=headers)
  return token.json()['access_token']


class CreatePaypalOrderView(generic.View):
  def post(self, request):
    order = get_or_set_order_session(request)
    token = PaypalToken()
    domain = request.build_absolute_uri('/')[:-1]
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token,
    }
    json_data = {
      "intent": "CAPTURE",
      "application_context": {
        "notify_url": domain,
        "return_url": domain,
        "cancel_url": domain,
        "brand_name": "Django Ecom",
        "landing_page": "BILLING",
        "shipping_preference": "NO_SHIPPING",
        "user_action": "CONTINUE"
      },
      "purchase_units": [
        {
          "reference_id": str(order),
          "description": ", ".join([item.product.description for item in order.items.all()]), # type: ignore
          # "custom_id": "",
          # "soft_descriptor": "",
          "amount": {
            "currency_code": "USD",
            "value": order.get_total()
          },
        }
      ]
    }

    response = requests.post('https://api-m.sandbox.paypal.com/v2/checkout/orders', headers=headers, json=json_data)
    # order_id = response.json()['id']
    # linkForPayment = response.json()['links'][1]['href']
    # return linkForPayment
    return JsonResponse(response.json())


class CapturePaypalOrderView(generic.View):
  def post(self, request):
    body = json.loads(request.body)
    order_id = body['orderID']
    token = PaypalToken()
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token,
    }
    response = requests.post(f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture', headers=headers)
    data = response.json()

    order = get_or_set_order_session(request)
    payment = Payment.objects.create(
      order=order,
      successful=True,
      raw_response=json.dumps(data),
      amount=float(data['purchase_units'][0]['payments']['captures'][0]['amount']['value']),
      payment_method='PayPal'
    )
    order.ordered = True
    order.ordered_date = datetime.datetime.today()
    order.save()

    return JsonResponse(data)


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
  template_name = 'order.html'
  context_object_name = 'order'

  def get_queryset(self):
    """Allow seeing all orders if `is_staff`, else limit to own orders."""
    if self.request.user.is_staff: # type: ignore
      return Order.objects.all()
    return Order.objects.filter(user=self.request.user)
  

class StripeCheckout(generic.View):
  def post(self, request):
    order = get_or_set_order_session(self.request)
    domain = request.build_absolute_uri('/')[:-1]
    line_items = [
      {
        'price_data': {
          'currency': 'USD',
          'unit_amount': int(item.get_raw_total_item_price()),
          'product_data': {
            'name': item.product.title,
            # 'metadata': {
            #   'color': item.color.name,
            #   'size': item.size.name,
            # }
          }
        },
        'quantity': item.quantity,
      }
      for item in order.items.all() # type: ignore
    ]
    # try:
    checkout_session = stripe.checkout.Session.create(
      line_items = line_items,
      mode = 'payment',
      success_url = domain + reverse('cart:thank-you'),
      cancel_url = domain + reverse('cart:payment'),
    )
    # except Exception as e:
    #   return str(e)

    return redirect(checkout_session.url)
