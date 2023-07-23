from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from cart.models import Order, Product
from .mixins import StaffUserMixin
from .forms import ProductForm


class StaffView(LoginRequiredMixin, StaffUserMixin, generic.ListView):
  template_name = 'staff/staff.html'
  queryset = Order.objects.filter(ordered=True).order_by('-ordered_date')
  paginate_by = 20
  context_object_name = 'orders'


class ProductListView(LoginRequiredMixin, StaffUserMixin, generic.ListView):
  template_name = 'staff/product_list.html'
  queryset = Product.objects.all()
  paginate_by = 20
  context_object_name = 'products'


class ProductDeleteView(LoginRequiredMixin, StaffUserMixin, generic.DeleteView):
  template_name = 'staff/product_delete.html'
  queryset = Product.objects.all()

  def get_success_url(self) -> str:
    return reverse('staff:product-list')


class ProductCreateView(LoginRequiredMixin, StaffUserMixin, generic.CreateView):
  template_name = 'staff/product_create.html'
  form_class = ProductForm

  def get_success_url(self) -> str:
    return reverse('staff:product-list')

  def form_valid(self, form) -> HttpResponse:
    form.save()
    return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, StaffUserMixin, generic.UpdateView):
  template_name = 'staff/product_update.html'
  queryset = Product.objects.all()
  form_class = ProductForm

  def get_success_url(self) -> str:
    return reverse('staff:product-list')

  def form_valid(self, form) -> HttpResponse:
    form.save()
    return super().form_valid(form)
  
