import os
import logging
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

        
class RegisterHandler(webapp2.RequestHandler):
    HANDLER_URL = '/'
    TEMPLATE = 'register.html'
    EDITABLE = ()
    
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        
        if self.request.get('logout') == '1':
            self.redirect(users.create_logout_url(self.__class__.HANDLER_URL))
            return
        
        entities = self._get_query(user).fetch()
        template_dict = {
            'title': 'Register context',
            'rows': entities,
            'menu': [
                {'url': self.__class__.HANDLER_URL, 'text':'List'},
                {'url':self.request.uri + '?logout=1','text':'Logout'},
            ],
        }
        
        template_path = os.path.join(os.path.dirname(__file__), 'templates', self.__class__.TENPLATE)
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
    
    def _get_query(self, user):
        return None
    
    def _add(self, user):
        return False
    
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
        if key:
            self._update(key.get())
            return True
        else:
            return False
    
    def _update(self, entity):
        for field in self.__class__.EDITABLE:
            entity.update_field(field, self._get_request_value(field))
        
        entity.put_if_updated()
    
    def _get_request_value(self, field):
        return self.request.get(field)
