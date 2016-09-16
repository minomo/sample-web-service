from google.appengine.ext import ndb


class BaseModel(ndb.Model):
    added_on = ndb.DateTimeProperty(auto_now_add = True)
    updated_on = ndb.DateTimeProperty(auto_now = True)
    
    @classmethod
    def insert(cls, key_name, **kwds):

        if not isinstance(key_name, basestring):
            raise TypeError('name must be a string; received %r' % key_name)
        elif not key_name:
            raise ValueError('name cannot be an empty string.')

        key = ndb.Key(cls, key_name, parent = kwds.get('parent'))
        
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
