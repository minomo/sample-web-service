import os
import logging
import json
import webapp2
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
import models
import register_handler

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

        template_path = os.path.join(
            os.path.dirname(__file__), 'templates', request_file_name)
        self.response.out.write(template.render(template_path, template_dict))


class RegistorContext(register_handler.RegisterHandler):
    HANDLER_URL = BASE_URL
    TENPLATE = 'register.html'

    def _get_query(self, user):
        return Context.query(Context.author == user)

    def _add(self, user):
        url = self.request.get('url')
        if not url:
            self.response.status = 400
            return False

        context = self._fetch_context(url)
        if context:
            result = Context.insert(url,
                                    title=self.request.get('title'),
                                    description=self.request.get(
                                        'description'),
                                    context=context,
                                    author=user,
                                    )

            if result is None:
                logging.info('deplicated')
                return False

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

        for field in ('title', 'description'):
            entity.update_field(field, self.request.get(field))

        context = self._fetch_context(key.id())
        entity.update_field('context', context)

        entity.put_if_updated()
        return True

    def _fetch_context(self, url):
        try:
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                if json.loads(result.content).get('@context'):
                    return result.content
            else:
                logging.error(
                    'Bad response from %s. status is %u'
                    % (url, result.status_code))

        except urlfetch.Error as e:
            logging.exception(e)


app = webapp2.WSGIApplication([
    (REGISTER_URL, RegistorContext),
    (BASE_URL + '(store\.(html|json-ld))?', StoreHandler),
], debug=True)
