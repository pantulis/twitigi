import sys
import logging

from google.appengine.ext import db
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.api.urlfetch import fetch as urlfetch, GET, POST

from demjson import decode as decode_json
from datetime import datetime, timedelta
from hashlib import sha1
from hmac import new as hmac

from random import getrandbits
from time import time
from urllib import urlencode, quote as urlquote
from uuid import uuid4

from environment import Environment
# ------------------------------------------------------------------------------
# configuration -- SET THESE TO SUIT YOUR APP!!
# ------------------------------------------------------------------------------

OAUTH_APP_SETTINGS = {

    'twitter': {
        'consumer_key': Environment.twitter_credentials()['consumer_key'],
        'consumer_secret': Environment.twitter_credentials()['consumer_secret'],
        'consumer_secret': 'i47YAhBhKi9KrWT8o00MAEeU4jBnAgSrKEpxDDIM8',
        'request_token_url': 'https://twitter.com/oauth/request_token',
        'access_token_url': 'https://twitter.com/oauth/access_token',
        'user_auth_url': 'http://twitter.com/oauth/authorize',
        'default_api_prefix': 'http://twitter.com',
        'default_api_suffix': '.json',
        }
    }

# ------------------------------------------------------------------------------
# utility functions
# ------------------------------------------------------------------------------

def get_service_key(service, cache={}):
    if service in cache: return cache[service]
    return cache.setdefault(
        service, "%s&" % encode(OAUTH_APP_SETTINGS[service]['consumer_secret'])
    )

def create_uuid():
    return 'id-%s' % uuid4()

def encode(text):
    return urlquote(str(text), '')

def twitter_specifier_handler(client):
    return client.get('/account/verify_credentials')['screen_name']

OAUTH_APP_SETTINGS['twitter']['specifier_handler'] = twitter_specifier_handler

# ------------------------------------------------------------------------------
# db entities
# ------------------------------------------------------------------------------

class OAuthRequestToken(db.Model):
    """OAuth Request Token."""
    service = db.StringProperty()
    oauth_token = db.StringProperty()
    oauth_token_secret = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    
class OAuthAccessToken(db.Model):
    """OAuth Access Token."""
    service = db.StringProperty()
    specifier = db.StringProperty()
    oauth_token = db.StringProperty()
    oauth_token_secret = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

# ------------------------------------------------------------------------------
# oauth client
# ------------------------------------------------------------------------------

class OAuthClient(object):

    __public__ = ('callback', 'cleanup', 'login', 'logout')

    def __init__(self, service, handler, oauth_callback=None, **request_params):
        self.service = service
        self.service_info = OAUTH_APP_SETTINGS[service]
        self.service_key = None
        self.handler = handler
        self.request_params = request_params
        self.oauth_callback = oauth_callback
        self.token = None

    # public methods

    def get(self, api_method, http_method='GET', expected_status=(200,), **extra_params):
        if not (api_method.startswith('http://') or api_method.startswith('https://')):
	            api_method = '%s%s%s' % (
                	self.service_info['default_api_prefix'], api_method,
	                self.service_info['default_api_suffix']
	                )

        if self.token is None:
            self.token = OAuthAccessToken.get_by_key_name(self.get_cookie())

        fetch = urlfetch(self.get_signed_url(
            api_method, self.token, http_method, **extra_params))

        if fetch.status_code not in expected_status:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )

        return decode_json(fetch.content)

    def post(self, api_method, http_method='POST', expected_status=(200,), **extra_params):

        if not (api_method.startswith('http://') or api_method.startswith('https://')):
            	api_method = '%s%s%s' % (
	                self.service_info['default_api_prefix'], api_method,
	                self.service_info['default_api_suffix']
	                )

        if self.token is None:
            self.token = OAuthAccessToken.get_by_key_name(self.get_cookie())

        fetch = urlfetch(url=api_method, payload=self.get_signed_body(
            api_method, self.token, http_method, **extra_params
            ), method=http_method)

        if fetch.status_code not in expected_status:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )
        return decode_json(fetch.content)

    def login(self):
        logging.debug("Estoy en login")
        proxy_id = self.get_cookie()
        logging.debug("self.get_cookie() == %s", proxy_id)

        if proxy_id:
            return "FOO%rFF" % proxy_id
            self.expire_cookie()
        return self.get_request_token()

    def logout(self, return_to='/'):
        self.expire_cookie()
        self.handler.redirect(self.handler.request.get("return_to", return_to))

    # oauth workflow

    def get_request_token(self):
        logging.debug("--> get_request_token()")
        token_info = self.get_data_from_signed_url(
            self.service_info['request_token_url'], **self.request_params
            )

        token = OAuthRequestToken(
            service=self.service,
            **dict(token.split('=') for token in token_info.split('&'))
            )

        token.put()

        if self.oauth_callback:
            oauth_callback = {'oauth_callback': self.oauth_callback}
        else:
            oauth_callback = {}

        self.handler.redirect(self.get_signed_url(
            self.service_info['user_auth_url'], token, **oauth_callback
           ))

    def callback(self, return_to='/'):
        oauth_token = self.handler.request.get("oauth_token")
        logging.debug("oauth_token  =%s", oauth_token)
        if not oauth_token:
            return get_request_token()

        oauth_token = OAuthRequestToken.all().filter(
            'oauth_token =', oauth_token).filter(
            'service =', self.service).fetch(1)[0]

        logging.debug("service_info['acces_token_url'] = %s", self.service_info['access_token_url'])
        token_info = self.get_data_from_signed_url(
            self.service_info['access_token_url'], oauth_token
            )
        logging.debug("token_info = %s", token_info)
        key_name = create_uuid()

        self.token = OAuthAccessToken(
            key_name=key_name, service=self.service,
            **dict(token.split('=') for token in token_info.split('&')))

        if 'specifier_handler' in self.service_info:
            specifier = self.token.specifier = self.service_info['specifier_handler'](self)
            logging.debug("specifier = %s", specifier)

            # FIXME esto peta
            #old = OAuthAccessToken.all().filter(
            #    'specifier =', specifier).filter(
            #    'service =', self.service)
            #if old:
            #    db.delete(old)

        self.token.put()
        self.set_cookie(key_name)
        self.handler.redirect(return_to)

    def cleanup(self):
        query = OAuthRequestToken.all().filter(
	            'created <', datetime.now() - EXPIRATION_WINDOW
	            )
        count = query.count(CLEANUP_BATCH_SIZE)
        db.delete(query.fetch(CLEANUP_BATCH_SIZE))
        return "Cleaned %i entries" % count

    # request marshalling
    def get_data_from_signed_url(self, __url, __token=None, __meth='GET', **extra_params):

        return urlfetch(self.get_signed_url(
            __url, __token, __meth, **extra_params
            )).content

    def get_signed_url(self, __url, __token=None, __meth='GET',**extra_params):
        return '%s?%s'%(__url, self.get_signed_body(__url, __token, __meth, **extra_params))

    def get_signed_body(self, __url, __token=None, __meth='GET',**extra_params):
        service_info = self.service_info

        kwargs = {
            'oauth_consumer_key': service_info['consumer_key'],
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_timestamp': int(time()),
            'oauth_nonce': getrandbits(64),
            }

        kwargs.update(extra_params)

        if self.service_key is None:
            self.service_key = get_service_key(self.service)

        if __token is not None:
            kwargs['oauth_token'] = __token.oauth_token
            key = self.service_key + encode(__token.oauth_token_secret)
        else:
            key = self.service_key

        message = '&'.join(map(encode, [
            __meth.upper(), __url, '&'.join(
                '%s=%s' % (encode(k), encode(kwargs[k])) for k in sorted(kwargs)
                )
            ]))

        kwargs['oauth_signature'] = hmac(
            key, message, sha1
            ).digest().encode('base64')[:-1]

        return urlencode(kwargs)

    # who stole the cookie from the cookie jar?

    def get_cookie(self):
        return self.handler.request.cookies.get(
            'oauth.%s' % self.service, ''
            )

    def set_cookie(self, value, path='/'):
        self.handler.response.headers.add_header(
            'Set-Cookie', 
            '%s=%s; path=%s; expires="Fri, 31-Dec-2021 23:59:59 GMT"' %
            ('oauth.%s' % self.service, value, path)
            )

    def expire_cookie(self, path='/'):
        self.handler.response.headers.add_header(
            'Set-Cookie', 
            '%s=; path=%s; expires="Fri, 31-Dec-1999 23:59:59 GMT"' %
            ('oauth.%s' % self.service, path)
            )


# ------------------------------------------------------------------------------
# oauth handler
# ------------------------------------------------------------------------------

class OAuthHandler(RequestHandler):

    def get(self, service, action=''):

        if service not in OAUTH_APP_SETTINGS:
            return self.response.out.write(
                "Unknown OAuth Service Provider: %r" % service
                )

        client = OAuthClient(service, self)

        if action in client.__public__:
            self.response.out.write(getattr(client, action)())
        else:
            self.response.out.write(client.login())

