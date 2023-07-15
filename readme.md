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

