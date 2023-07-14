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
