#!/usr/bin/env python

import logging
import sys
import os
import re
import string

from os.path import dirname, join as join_path
sys.path.insert(0, join_path(dirname(__file__), 'lib')) # extend sys.path

from wsgiref.handlers import CGIHandler
import wsgiref.handlers
import yaml


from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext import webapp, db
from google.appengine.api import users
from google.appengine.ext.webapp import template

from oauth import OAuthHandler, OAuthClient


class TUrl(db.Model):
        # user = db.ReferenceProperty(TUser, collection_name = 'twitted_urls') # Twitigi user who received this tweet
        twitter_id = db.IntegerProperty(required=True)

        text = db.StringProperty(required=True) # text body for the tweet 
        url = db.StringProperty()               # URL appearing in text body
        real_url = db.StringProperty()          # canonical URL after redirection
        title = db.StringProperty()             # value of title tag
        klass = db.StringProperty()             # classification for this tweet (photo, news, video, social, other)
        
        screen_name = db.StringProperty()       # who tweeted this
        public_name = db.StringProperty()
        profile_image_url = db.StringProperty()

        created_at = db.DateTimeProperty(auto_now_add=True)
        updated_at = db.DateTimeProperty(auto_now=True)
