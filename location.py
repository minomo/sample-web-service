#!/usr/bin/env python
import os
import logging
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
import webapp2
import models
import register_handler

BASE_URL = '/devices/'
REGISTER_URL = BASE_URL + 'register'

class Device(models.BaseModel):
    author = ndb.UserProperty()
    status = ndb.IntegerProperty()
    title = ndb.TextProperty()
    description = ndb.TextProperty()


class DeviceHandler(webapp2.RequestHandler):
    
    def get(self, urlsafe):
        if urlsafe:
            entity = ndb.Key(urlsafe = urlsafe).get()
            if entity:
                template_dict = {
                    'endpoint': self.request.url,
                    'title': entity.title,
                    'entity': entity,
                    'menu': [
                        {'url': REGISTER_URL, 'text':'Register'},
                    ],
                }
                
                template_path = os.path.join(os.path.dirname(__file__), 'templates', 'device.html')
                self.response.out.write(template.render(template_path, template_dict))
    
    def post(self, urlsafe):
        if urlsafe:
            entity = ndb.Key(urlsafe = urlsafe).get()
        
        if not entity:
            self.response.status = 400
            return
        
        email = entity.author.email()
        lon = self.request.get('lon') or self.request.get('lng') or self.request.get('longitude')
        lat = self.request.get('lat') or self.request.get('latitude')


class RegisterDevice(register_handler.RegisterHandler):
    TENPLATE = 'register_device.html'
    EDITABLE = ('title', 'description')
    
    def _get_query(self, user):
        return Device.query(Device.author == user)
    
    def _add(self, user):
        result = Device(
            title = self.request.get('title'),
            description = self.request.get('description'),
            author = user,
        ).put()
        
        if result is None:
            logging.info('Device add fail')
            return False
        
        return True


app = webapp2.WSGIApplication([
    (REGISTER_URL, RegisterDevice),
    (BASE_URL + '([\w-]+)', DeviceHandler),
], debug = True)
