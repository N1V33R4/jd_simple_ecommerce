# Project setup
## Secure settings
**static**: 
```py
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```
**database**: 2 configs, doesn't use dj_database_url like locallibrary
```py
if DEBUG is False:
  ...
  DATABASES = {
    'default': {
      'ENGINE': 'django.db.backends.postgresql_psycopg2',
      'NAME': '',
      'USER': '',
      'PASSWORD': '',
      'HOST': '',
      'PORT': '',
    }
  }
```
**allowed host**: host that's allowed to connect with your app(?)
```py
if DEBUG is False:
  ...
  ALLOWED_HOSTS = ['www.domain.com']
```
**secure headers**: idk what this all means
```py
if DEBUG is False:
  ...
  SESSION_COOKIE_SECURE = True
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NO_SNIFF = True
  SECURE_HSTS_INCLUDE_SUBDOMAIN = True
  SECURE_HSTS_SECONDS = 31536000
  SECURE_REDIRECT_EXEMPT = []
  SECURE_SSL_REDIRECT = True
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```
**email backend**: 2 configs
```py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if DEBUG is False:
  ...
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

I don't like downloading environ, seems deprecated. 
`dotenv` seems to be a better alternative. 

## Project files
When I think about it, I tend to copy paste a lot of backend logic between projects. Can't I do the same with CSS? :)

I just downloaded static/ from master branch. 

The include tag is interesting. 

## Home view
`TemplateView`: simply renders template(?)

## Contact view
`FormView`: view that renders a template alongside form(?)  
form's widget: can choose which type of input field to use to render  
&emsp;can also add attrs={} for various html attributes  
- `get_success_url()`: overwrite redirect on form success 

`django-cripsy-forms`: lib for nice forms
```shell
pip install crispy_forms
pip install crispy_bootstrap5
```
```py
INSTALLED_APPS = (
  ...
  "crispy_forms",
  "crispy_bootstrap5",
  ...
)
CRISPY_TEMPLATE_PACK = "bootstrap5"
```
See more [crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/index.html), [crispy_bootstrap5](https://github.com/django-crispy-forms/crispy-bootstrap5)

`messages`: send message after form submission(or sth)
```py
from django.contrib import messages
...
messages.info(self.request, message)
```

`send_mail`: 
```py
from django.core.mail import send_mail
...
send_mail(
  'Received contact form submission',
  full_message,
  from_email=settings.DEFAULT_FROM_EMAIL,
  recipient_list=[settings.NOTIFY_EMAIL]
)
```

Using `dotenv`: 
```shell
pip install python-dotenv
```
```py
from dotenv import load_dotenv
load_dotenv()
SOME_KEY = os.getenv('SOME_KEY')
```


# Business logic
## Initial models
new app 'cart'
`related_name` in foreign key: allows you to use a diff name instead of `sth_set`

My god, you can simply have multiple fields in one table reference one other table. It's much simpler than Many-to-many when you want a limited number of references! 

**namespace in `include()`**: can add namespace when including urls from an app. Useful for referencing urls from inside templates(?)  
Can use: `{% url 'cart:product-list' %}`

Isn't `OrderItem` a many-to-many relation with additional fields??? Wtf have I been smoking to not notice that and used such an obscure many-to-many field instead of creating a table on my own during my Laravel test?   
Is this what experience and failure teaches? Damn, so valuable. 

## Product list view
**Image uploads**: `ImageField` set `upload_to` to where you want the files to stay  
ex: if `uploaded_to='product_images'`, and `MEDIA_ROOT='media'`, the files will be uploaded to `project_root/media/product_images/...`
&emsp;use by `{{ obj.image.url }}`

## Product detail view
Bootstrap columns make it really easy to structure your layout. 

Why is there `queryset` in `DetailView`? 

## Add to cart view
**Filter and get one**: 
```py
order = Order.objects.get(id=order_id, ordered=False)
```

**Cart without login**: can set `order_id` to session and attach a user if logged in later. 

`ModelForm`
- save(): saves the model it represents into db, `commit=False` makes it just return the obj

`FormView`: I guess it simplifies the GET and POST aspect of the form for you? 
- get_success_url: redirect to url on success
- get_context_data: run on get
- form_valid: run on post

## Item variations
Overriding `__init__` in ModelForm: to allow passing additional data to limit choice field for example   
Overriding `get_form_kwargs` in FormView: to pass data to form obj when created 

No wonder django uses "ForeignKey", it doesn't necessarily indicate many-to-one relationship, sometimes you just want to reference a key from another table. 

Product variations (color, size) are many-to-many?? idk it was that way. 

## Cart view (order detail)
Just a simpe TemplateView to list details of an order. 

You don't really need to protect this view 'cuz the order (cart) id is from the user's sessions! 

## Pricing
Better to store price as int 'cuz float calculation errors. Store in cents, do logic when displaying. 

## Cart view actions
`generic.View`: only has get/post(?)
```py
def get(self, request, *args, **kwargs):
```

Using get is better 'cuz of easy navigation? 

## Cart totals
**Aggregation: Summation of Multiplication of two fields**:  
```py
def get_raw_subtotal(self) -> int:
  sum = Order.objects.aggregate(subtotal=Sum(F('items__quantity') * F('items__product__price')))
  return sum['subtotal']
```
> I found this out after googling and caring about performance
> course taught me application level

**Creating custom template filters**: for cart count 'cuz base.html doesn't know our order  
Takes request and spits out `OrderItem` count
```py
from django import template
from cart.utils import get_or_set_order_session

register = template.Library()

@register.filter
def cart_item_count(request) -> int:
  order = get_or_set_order_session(request)
  count = order.items.count() # type: ignore
  return count
```

Use:
```html
{% load cart_template_tags %}

{{ request|cart_item_count }}
```

## Checkout view
Issue right now: user gets new cart when logout and login again. Possibly due to utils function being called in `base.html`, and the fact that your session gets WIPED after logout! Leads to a lot of stale carts too, smh

Also the problem with nullables are the same with Python as with Java, EVERY F*CKING THING IS NULLABLE. Web apps are 

**Using `forms.Form`**: flexible, use whatever fields you like, can pass id into form for filtering choices fields.  
Can do custom validation in `clean()`: i.e. make certain fields required if you don't select choice 
```py

```
Then you can do whatever you want with the validated data.  

The more I get into this, the more I disagree with the instructor's choices. 

## Payments with paypal 
Embed buttons in our page, redirect to paypal.  

Create paypal business account.  
Set paypal client_id and secret key (for dev and prod).  
Add js sdk, render buttons, update actions 

Turns out the course has (going to be) depracated paypal api usage, so I had to do it on my own. Shit's real. It's all restful now. 

**Get domain in view**: 
```py
domain = request.build_absolute_uri('/')[:-1]
```

**Send CSRF token with JS fetch**: add this to script
```js
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie('csrftoken');
```

How paypal integration works: 
1. buttons send requests to our server
2. server sends requests to Paypal's API with token created by client_id and secret_key
3. server returns json returned from Paypal's API, do stuff in between (like store result in db)

**Read json data from post request in view**: it's NOT IN `request.POST`  
You have to read it from `request.body`
```py
import json
json_data = json.loads(request.body)
```

You register 2 events on for the buttons:
1. createOrder: when user clicks on paypal button(?)
   sends post request to server, server sends post request to paypal api
   server returns order from paypal api, event returns order.id
2. onApprove: when user clicks pay(?)
   sends post request to server, server sends post request to paypal api and store payment information in db. then sends back json to client

## Auth and user profile
