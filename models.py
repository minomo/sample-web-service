# Original code of this file was published under the following lisence at
# https://github.com/google/physical-web/
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import ndb


class BaseModel(ndb.Model):
    added_on = ndb.DateTimeProperty(auto_now_add=True)
    updated_on = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kwds):
        super(BaseModel, self).__init__(*args, **kwds)
        self._updated = False

    @classmethod
    def insert(cls, key_name, **kwds):

        if not isinstance(key_name, basestring):
            raise TypeError('name must be a string; received %r' % key_name)
        elif not key_name:
            raise ValueError('name cannot be an empty string.')

        key = ndb.Key(cls, key_name, parent=kwds.get('parent'))

        @ndb.tasklets.tasklet
        def internal_tasklet():
            @ndb.tasklets.tasklet
            def txn():
                entity = yield key.get_async()
                if entity is not None:
                    raise ndb.tasklets.Return(None)

                entity = cls(**kwds)
                entity._key = key
                fut = yield entity.put_async()
                raise ndb.tasklets.Return(fut)

            if ndb.model.in_transaction():
                fut = yield txn()
            else:
                fut = yield ndb.model.transaction_async(txn)

            raise ndb.tasklets.Return(fut)

        return internal_tasklet().get_result()

    def get(self, name):
        prop = self._properties.get(name)
        if isinstance(prop, ndb.Property):
            return prop._get_value(self)
        else:
            return None

    def update_field(self, name, value):
        if value is None:
            return

        prop = self._properties.get(name)
        if isinstance(prop, ndb.Property):
            if isinstance(prop, ndb.IntegerProperty):
                value = int(value)

            if value != prop._get_value(self):
                prop._set_value(self, value)
                self._updated = True

    def put_if_updated(self):
        if self._updated:
            self.put()
