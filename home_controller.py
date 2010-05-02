#!/usr/bin/env python

import logging
import sys
import os
import re
import string
from environment import Environment
from os.path import dirname, join as join_path
sys.path.insert(0, join_path(dirname(__file__), 'lib')) # extend sys.path

from wsgiref.handlers import CGIHandler
import wsgiref.handlers
import yaml

from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext import webapp, db
from google.appengine.api import users
from google.appengine.ext.webapp import template

from tuser import TUser
from oauth import OAuthHandler, OAuthAccessToken, OAuthClient

class HomeHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        tuser = TUser.get_or_insert(user.user_id(), 
                                    user_id=user.user_id())
        client = OAuthClient('twitter',self)
        
        if tuser.access_token is None:
            if client.get_cookie():
                logging.debug("registered user finished oauth procedure")

                credentials = client.get('/account/verify_credentials')
                tuser.access_token = OAuthAccessToken.get_by_key_name(client.get_cookie())
                tuser.screen_name = credentials['screen_name']
                tuser.profile_image_url = credentials['profile_image_url']
                tuser.name = credentials['name']
                tuser.put()
                view = 'just_logged.html'
                template_values = {
                    'username':user.nickname(),
                    'email':user.email()
                    }
            else:
                view = 'not_logged.html'
                template_values = {
                    'username': user.nickname(),
                    'email': user.email()
                    }
        else:
            view = 'index.html'

        path = os.path.join(os.path.dirname(__file__) + '/templates/' + view )
        self.response.out.write(template.render(path, template_values))
            
    def twitter_infos(self, client):
        twit_infos = []
        the_twits = client.get('/statuses/friends_timeline', 'GET', (200,),count=200)
        url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
        for twit in the_twits:
            if (re.search("http", twit['text'])):
                twit_info = {}
                twit_info['username'] = twit['user']['screen_name']
                twit_info['content'] = url_regex.sub(r'<a href="\1">\1</a>', twit['text'])
                twit_infos.append(twit_info)
                
        return twit_infos
