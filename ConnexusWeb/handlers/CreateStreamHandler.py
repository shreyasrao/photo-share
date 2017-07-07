import webapp2
import jinja2
import json
import cgi
import datetime
from google.appengine.ext import ndb
from handlers.Stream import Stream
from google.appengine.api import mail
from google.appengine.api import users
from BaseHandler import BaseHandler

#/create_stream
class CreateStreamHandler(webapp2.RequestHandler, BaseHandler):

    def get(self):
        self.cache("create")
        JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates'),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

        template = JINJA_ENVIRONMENT.get_template('CreateStreamPage.html')
        self.response.write(template.render())

    def post(self):
        JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates'),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

        #Get the stream's data
        stream_name = cgi.escape(self.request.get('stream_name'))
        subscribers_string = cgi.escape(self.request.get('subscribers'))
        message = cgi.escape(self.request.get('message'))
        tags_string = cgi.escape(self.request.get('tags'))
        cover_image = cgi.escape(self.request.get('cover_image'))

        subscribers = [x.strip() for x in subscribers_string.split(',')]
        tags = [x.strip() for x in tags_string.split(',')]

        #Send emails to all subscribers
        email = mail.EmailMessage()
        user = users.get_current_user()
        email.sender = user.email()
        email.subject = "'Notification of Subscription to %s'" % stream_name
        email.body = message
        subscriber_ids=[]
        for subscriber in subscribers:
            if len(subscriber)!=0:
                sub_id = users.User(subscriber).user_id()
                subscriber_ids.append("%s" % sub_id)
                email.to = "%s" % subscriber
                email.send()

        #stream already exists
        if not stream_name:
            self.redirect('/error')
        stream = Stream.query(Stream.name == stream_name).get()
        if stream:
            self.redirect('/error')
        else :
            #Create a new stream with name, no photos, and no views initially
            #Add stream to the datastore
            user = users.get_current_user()
            new_stream = Stream(owner_id = user.user_id(),name=stream_name,photos=[], num_photos = 0, views=0,  view_queue=[],
                                subscribed_users=subscriber_ids,timestamp = datetime.datetime.now(), tags = tags, cover_image=cover_image,
                                email=user.email())
            new_stream.key = ndb.Key(Stream, stream_name)
            new_stream.put()

            #encure redict happens after data store is updated
            jobDone = False
            while(not jobDone):
                search_results = Stream.query(Stream.name == stream_name)
                for search in search_results:
                    jobDone = True

            self.redirect('/management')
