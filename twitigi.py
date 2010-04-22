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

from home_controller import HomeHandler
from update_controller import UpdateHandler

_DEBUG = True

def main():
        logging.getLogger().setLevel(logging.DEBUG)
        application = webapp.WSGIApplication([
                        ('/oauth/(.*)/(.*)', OAuthHandler),
                        ('/update', UpdateHandler),
                        ('/', HomeHandler)
                        ], debug=True)
        
        wsgiref.handlers.CGIHandler().run(application)	
        
if __name__ == '__main__': main()
