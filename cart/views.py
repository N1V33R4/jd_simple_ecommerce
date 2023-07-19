from typing import Any, Dict
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.contrib import messages
from .models import Product, OrderItem, Address
from .utils import get_or_set_order_session
from .forms import AddToCartForm, AddressForm


class ProductListView(generic.ListView):
  template_name = 'cart/product_list.html'
  queryset = Product.objects.all()


class ProductDetailView(generic.FormView):
  template_name = 'cart/product_detail.html'
  form_class = AddToCartForm
  
  def get_object(self):
    return get_object_or_404(Product, slug=self.kwargs['slug'])

  def get_success_url(self) -> str:
    return reverse('home') # TODO: cart
  
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
    return reverse('home') # TODO: payment

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
