import os
import logging
import json
import webapp2
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
import models


BASE_URL = '/contexts/'
REGISTER_URL = BASE_URL + 'register'

class Context(models.BaseModel):
    author = ndb.UserProperty()
    title = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    context = ndb.TextProperty()


class StoreHandler(webapp2.RequestHandler):

    def get(self, request_file_name, ext):
        entities = Context.query().fetch()
        template_dict = {
            'title': 'Context Store',
            'menu': [{'url': REGISTER_URL, 'text': 'Register'}],
            'rows': entities,
        }
        
        if request_file_name is None:
            request_file_name = 'store.html'
        elif request_file_name == 'store.json-ld':
            self.response.headers['Content-Type'] = 'application/json'
        
        template_path = os.path.join(os.path.dirname(__file__), 'templates', request_file_name)
        self.response.out.write(template.render(template_path, template_dict))


class RegistorContext(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        
        if self.request.get('logout') == '1':
            self.redirect(users.create_logout_url(BASE_URL))
            return
        
        entities = Context.query(Context.author == user).fetch()
        template_dict = {
            'title': 'Register context',
            'rows': entities,
            'menu': [
                {'url': BASE_URL, 'text':'List'},
                {'url':self.request.uri + '?logout=1','text':'Logout'},
            ],
        }
        
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'register.html')
        self.response.out.write(template.render(template_path, template_dict))
    
    def post(self):
        user = users.get_current_user()
        if not user:
            self.response.status = 403
            return
        
        action = self.request.get('action')
        result = False
        if action == 'delete':
            result = self._delete(user)
        elif action == 'edit':
            result = self._edit(user);
        else:
            result = self._add(user)
        
        if result:
            self.redirect(self.request.url)
    
    def _add(self, user):
        url = self.request.get('url')
        if not url:
            self.response.status = 400
            return False
        
        context = self._fetch_context(url)
        if context:
            result = Context.insert(url,
                title = self.request.get('title'),
                description = self.request.get('description'),
                context = context,
                author = user,
            )
            
            if result is None:
                logging.info('deplicated')
                return False
            
        return True
    
    def _get_key(self):
        url_string = self.request.get('key')
        if not url_string:
            self.response.status = 400
            return None
        
        return ndb.Key(urlsafe = url_string)
    
    def _delete(self, user):
        key = self._get_key()
        if not key:
            return False
        
        result = key.delete()
        if result is not None:
            logging.debug(result)
        
        return True
    
    def _edit(self, user):
        key = self._get_key()
        if not key:
            return False
        
        entity = key.get()
        
        url = self.request.get('url')
        if url and url != key.id():
            key.delete()
            self._add(user)
            return True
        
        do_update = False
        title = self.request.get('title')
        if title and title != entity.title:
            entity.title = title
            do_update = True
        
        description = self.request.get('description')
        if description and entity.description != description:
            entity.description = description
            do_update = True
        
        context = self._fetch_context(key.id())
        if context and context != entity.context:
            entity.context = context
            do_update = True
        
        if do_update:
            entity.put()
        
        return True
    
    def _fetch_context(self, url):
        try:
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                if json.loads(result.content).get('@context'):
                    return result.content
            else:
                logging.error('Bad response from %s. status is %u' % (url, result.status_code))
        
        except urlfetch.Error as e:
            logging.exception(e)


app = webapp2.WSGIApplication([
    (REGISTER_URL, RegistorContext),
    (BASE_URL + '(store\.(html|json-ld))?', StoreHandler),
], debug = True)
