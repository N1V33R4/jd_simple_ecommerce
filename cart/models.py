from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from django.db.models.signals import pre_save
from django.urls import reverse
from django.utils.text import slugify

User = get_user_model()


class Category(models.Model):
  name = models.CharField(max_length=100)
  
  def __str__(self) -> str:
    return self.name

  class Meta:
    verbose_name_plural = 'Categories'


class Address(models.Model):
  ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
  )

  user = models.ForeignKey(User, on_delete=models.CASCADE)
  address_line_1 = models.CharField(max_length=150)
  address_line_2 = models.CharField(max_length=150)
  city = models.CharField(max_length=100)
  zip_code = models.CharField(max_length=20)
  address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
  default = models.BooleanField(default=False)

  def __str__(self):
    return f"{self.address_line_1}, {self.address_line_2}, {self.city}, {self.zip_code}"
  
  class Meta:
    verbose_name_plural = 'Addresses'


class ColorVariation(models.Model):
  name = models.CharField(max_length=50)

  def __str__(self) -> str:
    return self.name


class SizeVariation(models.Model):
  name = models.CharField(max_length=50)

  def __str__(self) -> str:
    return self.name


class Product(models.Model):
  title = models.CharField(max_length=150)
  slug = models.SlugField(unique=True)
  image = models.ImageField(upload_to='product_images')
  description = models.TextField()
  price = models.IntegerField(default=0) # in cents, e.g. $10.75 = 1075
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  active = models.BooleanField()
  available_colors = models.ManyToManyField(ColorVariation)
  available_sizes = models.ManyToManyField(SizeVariation)
  primary_category = models.ForeignKey(
    Category,
    related_name='primary_products',
    on_delete=models.CASCADE)
  secondary_categories = models.ManyToManyField(Category, blank=True)

  def __str__(self):
    return self.title
  
  def get_absolute_url(self):
    return reverse("cart:product-detail", kwargs={"slug": self.slug})
  
  def get_delete_url(self):
    return reverse("staff:product-delete", kwargs={"pk": self.pk})
  
  def get_update_url(self):
    return reverse("staff:product-update", kwargs={"pk": self.pk})
  
  def get_price(self):
    return "{:.2f}".format(self.price / 100)


class OrderItem(models.Model):
  order = models.ForeignKey("Order", related_name="items", on_delete=models.CASCADE)
  product = models.ForeignKey(Product, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField(default=1)
  color = models.ForeignKey(ColorVariation, on_delete=models.CASCADE)
  size = models.ForeignKey(SizeVariation, on_delete=models.CASCADE)

  def __str__(self):
    return f"{self.quantity} x {self.product}"
  
  def get_raw_total_item_price(self):
    return self.quantity * self.product.price
  
  def get_total_item_price(self):
    price = self.get_raw_total_item_price()
    return "{:.2f}".format(price / 100)
  

class Order(models.Model):
  user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
  start_date = models.DateTimeField(auto_now_add=True)
  ordered_date = models.DateTimeField(blank=True, null=True)
  ordered = models.BooleanField(default=False)

  billing_address = models.ForeignKey(
    Address, related_name='billing_address', blank=True, null=True, on_delete=models.SET_NULL)
  shipping_address = models.ForeignKey(
    Address, related_name='shipping_address', blank=True, null=True, on_delete=models.SET_NULL)

  def __str__(self):
    return self.reference_number
  
  @property
  def reference_number(self):
    return f"ORDER-{self.pk}"
  
  def get_raw_subtotal(self) -> int:
    sum = OrderItem.objects.filter(order__id=self.id).aggregate(subtotal=Sum(F('quantity') * F('product__price'))) # type: ignore
    return sum['subtotal'] or 0
  
  def get_subtotal(self):
    subtotal = self.get_raw_subtotal()
    return "{:.2f}".format(subtotal / 100)
  
  def get_raw_total(self):
    subtotal = self.get_raw_subtotal()
    # total = subtotal - discounts + tax + delivery
    return subtotal
  
  def get_total(self):
    total = self.get_raw_total()
    return "{:.2f}".format(total / 100)


class Payment(models.Model):
  order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
  payment_method = models.CharField(max_length=20, choices=(
    ('PayPal', 'PayPal'),
  ))
  timestamp = models.DateTimeField(auto_now_add=True)
  successful = models.BooleanField(default=False)
  amount = models.FloatField()
  raw_response = models.TextField()

  def __str__(self):
    return self.reference_number
  
  @property
  def reference_number(self):
    return f"PAYMENT-{self.order}-{self.pk}"
  

def pre_save_product_receiver(sender, instance: Product, *args, **kwargs):
  if not instance.slug:
    instance.slug = slugify(instance.title)

pre_save.connect(pre_save_product_receiver, sender=Product)
