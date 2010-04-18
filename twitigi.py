#!/usr/bin/env python

import sys
import os
import re
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


class MyIndexHandler(webapp.RequestHandler):
	def get(self):
		client = OAuthClient('twitter', self)
                
                if not client.get_cookie():
                        view = 'not_logged.html'
                        template_values = {}
                else:
                        template_values = {
                                'username': client.get('/account/verify_credentials')['screen_name'],
                                # 'twits': client.get('/statuses/friends_timeline', 'GET', (200,), count = 100)
                                'twits': self.get_twits_with_url(client)
                                }
                        view = 'index.html'

                path = os.path.join(os.path.dirname(__file__) + '/templates/' + view )
                self.response.out.write(template.render(path, template_values))

        def  get_twits_with_url(self, client):
                my_twits = client.get('/statuses/friends_timeline', 'GET', (200,), count = 1000)
                the_twits = []
                url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
                for twit in my_twits:
                        if (re.search("http", twit['text'])):
                            twit['text'] = url_regex.sub(r'<a href="\1">\1</a>', twit['text'])
                            the_twits.append(twit)
                return the_twits
                        
        def twitter_feeds(self, client):
            the_twits = client.get('/statuses/friends_timeline', 'GET', (200,), count=100)
            res = "<ul>"
            url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
            for twit in the_twits:
                twit_username = twit['user']['screen_name']
                twit_content = twit['text']

                if (re.search("http", twit_content)):
                    res += "<li>"
                    res += "<strong>" + twit_username + "</strong> : " + url_regex.sub(r'<a href="\1">\1</a>', twit_content)
                    res += "</li>"

            res += "</ul>"
            return res


def main():
	application = webapp.WSGIApplication([
                ('/oauth/(.*)/(.*)', OAuthHandler),
                ('/', MyIndexHandler)
        ], debug=True)
        
	wsgiref.handlers.CGIHandler().run(application)	

if __name__ == '__main__': main()
