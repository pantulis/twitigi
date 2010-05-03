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
        if self.access_token:
            logging.debug ("TUser::access_token = %s", self.access_token)
            client.token = self.access_token
            the_twits = client.get('/statuses/friends_timeline','GET', (200,),count=200)
            url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
            for twit in the_twits:
                if (re.search("http", twit['text'])):
                    twit_id = twit['id']
                    twit_text = twit['text']
                    twit_url = TUrl.extract_url_from_text(twit['text'])
                    screen_name = twit['screen_name']
                    public_name = twit['public_name']
                    profile_image_url = twit['profile_image_url']
                    
                    logging.debug("    --> twitter_id = %s", twit_id)
                    logging.debug("    --> twitter_text = %s", twit_text)
                    logging.debug("    --> twit_url = %s", twit_url)
                    logging.debug("    --> screen_name = %s", screen_name)
                    logging.debug("    --> public_name = %s", public_name)
                    logging.debug("    --> profile_image_url = %s", profile_image_url)

                    #turl = TUrl.get_or_insert(twit_id,
                    #                          text = twit_text,
                    #                         url = twit_url,
                    #                          screen_name = twit['screen_name'],

        else:
            logging.debug("TUser: access_token is nil!")



    
