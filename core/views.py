from typing import Any
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from .forms import ContactForm
from cart.models import Order


class HomeView(generic.TemplateView):
  template_name = 'index.html'


class ContactView(generic.FormView):
  form_class = ContactForm
  template_name = 'contact.html'

  def get_success_url(self) -> str:
    return reverse('contact')
  
  # data is already cleaned right?
  def form_valid(self, form: Any) -> HttpResponse:
    messages.info(self.request, 'Thanks for getting in touch. We have received your message.')
    name = form.cleaned_data.get('name')
    email = form.cleaned_data.get('email')
    message = form.cleaned_data.get('message')

    full_message = f"""
      Received messsage below form {name}, {email}
      __________________________


      {message}
    """
    send_mail(
      'Received contact form submission',
      full_message,
      from_email=settings.DEFAULT_FROM_EMAIL,
      recipient_list=[settings.NOTIFY_EMAIL]
    )

    return super().form_valid(form)


class ProfileView(LoginRequiredMixin, generic.TemplateView):
  template_name = 'profile.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      "orders": Order.objects.filter(user=self.request.user, ordered=True)
    })
    return context
  