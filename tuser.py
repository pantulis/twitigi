#!/usr/bin/env python

import logging
import re
import string



from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext import webapp, db
from google.appengine.api import users
from google.appengine.ext.webapp import template

from oauth import OAuthClient
from turl import TUrl

class TUser(db.Model):
    user_id = db.StringProperty(required = True)
    twitter_id = db.IntegerProperty()
    screen_name = db.StringProperty()
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    profile_image_url = db.StringProperty()
    access_token = db.ReferenceProperty()

    def fetch_twits(self):
        logging.debug("user(%s)::fetch_twits", self.user_id)
        client = OAuthClient('twitter',self)
        client.token = self.access_token
        the_twits = client.get('/statuses/friends_timeline','GET', (200,),count=200)
        url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
        for twit in the_twits:
            if (re.search("http", twit['text'])):
                twit_id = twit['id']
                twit_text = twit['text']

                logging.debug("    --> twitter_id = %s", twit_id)
                logging.debug("    --> twitter_text = %s", twit_text)
                




    
