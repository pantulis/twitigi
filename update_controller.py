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
from tuser import TUser

class UpdateHandler(webapp.RequestHandler):
    def get(self):

        tusers = TUser.all().fetch(10)
        for u in tusers:
            u.fetch_twits()
            
            
