#!/usr/bin/env python
import logging
import os
import webapp2
from google.appengine.api import app_identity, mail
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
import helpers
import models
import register_handler

APP_ID = app_identity.get_application_id()
BASE_URL = '/devices/'
REGISTER_URL = BASE_URL + 'register'

class Device(models.BaseModel):
    author = ndb.UserProperty()
    status = ndb.IntegerProperty()
    title = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    url = ndb.StringProperty(indexed=False)


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
        
        mail.send_mail(
            sender = 'noreply@%s.appspotmail.com' % APP_ID,
            to = email,
            subject = 'Location of your device',
            body = 'Longitude:' + lon + 'Latitude:' + lat)


class RegisterDevice(register_handler.RegisterHandler):
    TENPLATE = 'register_device.html'
    EDITABLE = ('title', 'description', 'status')
    
    def _get_query(self, user):
        return Device.query(Device.author == user)
    
    def _add(self, user):
        entity = Device(
            title = self.request.get('title'),
            description = self.request.get('description'),
            status = self._get_request_value('status'),
            author = user,
        )
        
        key = entity.put()
        if key is None:
            logging.info('Device add fail')
            return False
        
        shortUrl = helpers.ShortenUrl(self.request.host_url + BASE_URL + key.urlsafe())
        if shortUrl:
            entity.url = shortUrl
            entity.put()
        
        return True
    
    def _get_request_value(self, field):
        value = self.request.get(field)
        if field == 'status':
            value = 1 if value else 0
        
        return value


app = webapp2.WSGIApplication([
    (REGISTER_URL, RegisterDevice),
    (BASE_URL + '([\w-]+)', DeviceHandler),
], debug = True)
