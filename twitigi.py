#!/usr/bin/env python

import logging
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


class TUser(db.Model):
        tid = db.IntegerProperty(required=True)

        screen_name = db.StringProperty(required=True)
        name = db.StringProperty(required = True)
        created = db.DateTimeProperty(auto_now_add = True)
        updated = db.DateTimeProperty(auto_now = True)
        profile_image_url = db.StringProperty()



        # we have more twits for this user, let's insert them into the DataStore
        def add_twits(self, twits):
                for twit in twits:
                        turl =  TUrl.find_or_create_by_twitter_id(twit['id'],
                                                                  twit['text'],
                                                                  twit['user']['screen_name'],
                                                                  twit['user']['profile_image_url']),
                        if self.key() not in turl.users:
                                turl.users.append(self.key())
                                turl.put()

        @property 
        def twits(self):
                return TUrl.gql("WHERE users = :1", self.key())

        @staticmethod
        def exists(tid):
                logging.debug("user_exists? %d", tid)
                users = db.Query(TUser,).filter('tid = ', tid)
                if users.count() != 0:
                        return users[0]
                else:
                        return None
                
        @staticmethod
        def find_or_create_by_twitter_id(twitter_id, screen_name, name):
                tuser = TUser.exists(twitter_id)
                if not tuser:
                        logging.debug("user does not exist, creating it")
                        tuser = TUser(tid = twitter_id,
                                      screen_name = screen_name,
                                      name = name)  # FIXME add avatar url
                        tuser.put()
                else:
                        logging.debug("user already exists, tid = %d, screen_name = %s, name = %s",
                                      tuser.tid, tuser.screen_name, tuser.name)
                        
                return tuser
              
class TUrl(db.Model):
        tid = db.IntegerProperty(required = True)
        text = db.StringProperty(required = True)
        url = db.StringProperty(required= True)
        real_url = db.StringProperty()
        title = db.StringProperty()
        klass = db.StringProperty()
        
        # who twitted this ?
        screen_name = db.StringProperty(required=True) 
        profile_image_url = db.StringProperty(required=True)

        created_at = db.DateTimeProperty(auto_now_add=True)
        updated_at = db.DateTimeProperty(auto_now = True)
        users = db.ListProperty(db.Key)

        @staticmethod
        def exists(tid):
                logging.debug("URL exists? %d", tid)
                urls = db.Query(TUrl,).filter('tid = ', tid)
                if urls.count() != 0:
                        return urls[0]
                else:
                        return None

        @staticmethod
        def find_or_create_by_twitter_id(twitter_id, text, screen_name, profile_image_url):
                turl = TUrl.exists(twitter_id)
                if not turl:
                        logging.debug("twit with url does not exist, creating it")
                        url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
                        text = url_regex.sub(r'<a href="\1">\1</a>', text)
                        url = url_regex.search(text).expand('\1')
                        logging.debug("la url es %s y el texto queda %s", url, text)

                        turl = TUrl(tid = twitter_id,
                                    text = text,
                                    url = url,
                                    screen_name = screen_name,
                                    users = [],
                                    profile_image_url = profile_image_url)
                        logging.debug("vacio la lista de users")

                        logging.debug("y lo guardo!")
                        turl.put()
                else:
                        logging.debug("url already exists, tid = %d, screen_name = %s, text = %s",
                                      turl.tid, turl.screen_name, turl.text)

                        
                logging.debug("TUrl.users = %s", turl.users)
                return turl


class MyIndexHandler(webapp.RequestHandler):
	def get(self):
		client = OAuthClient('twitter', self)
                
                if not client.get_cookie():
                        view = 'not_logged.html'
                        template_values = {}
                else:
                        credentials = client.get('/account/verify_credentials')
                        tuser = TUser.find_or_create_by_twitter_id(int(credentials['id']),
                                                                   credentials['screen_name'],
                                                                   credentials['name'])
                        twits = self.get_twits_with_url(client)
                        tuser.add_twits(twits)
                        template_values = {
                                'username': client.get('/account/verify_credentials')['screen_name'],
                                'twits'   : tuser.twitted_urls # FIXME update TUser.twitted_urls sometime
                                }
                        view = 'index.html'

                path = os.path.join(os.path.dirname(__file__) + '/templates/' + view )
                self.response.out.write(template.render(path, template_values))

        def  get_twits_with_url(self, client):
                my_twits = client.get('/statuses/friends_timeline', 'GET', (200,), count = 1000)
                the_twits = []
                url_regex = re.compile(r'''((?:mailto:|ftp://|http://)[^ <>'"{}|\\^`[\]]*)''')
                for twit in my_twits:
                        if (url_regex.search(twit['text'])):
                            #twit['text'] = url_regex.sub(r'<a href="\1">\1</a>', twit['text'])
                            the_twits.append(twit)
                return the_twits
                        

def main():
        logging.getLogger().setLevel(logging.DEBUG)
	application = webapp.WSGIApplication([
                ('/oauth/(.*)/(.*)', OAuthHandler),
                ('/', MyIndexHandler)
        ], debug=True)
        
	wsgiref.handlers.CGIHandler().run(application)	

if __name__ == '__main__': main()
