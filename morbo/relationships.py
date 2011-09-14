from pymongo.objectid import ObjectId
import importlib


class Relationship(object):
    
    def __init__(self, model, embedded=False, cascade=False, instance_class=None):
        self.model = model
        self.embedded = embedded
        self.cascade = cascade
        self.instance_class = None
        
        
    def get_model(self):
        if isinstance(self.model, basestring):
            parts = self.model.split('.')
            n = parts.pop()
            m = importlib.import_module('.'.join(parts))
            print m
            self.model = getattr(m, n)
        return self.model
        
        
    def get_default_field_name(self, plural=False):
        name = self.model if isinstance(self.model, basestring) else self.model.__name__
        name = name.lower()
        
        if self.embedded:
            if plural:
                name += 'es' if name[-1] == 's' else 's'
        else:
            if plural:
                name += '_ids'
            else:
                name += '_id'
        
        return name
        
        
    def get(self, owner):
        raise NotImplementedError
        
        
    def set(self, owner, obj):
        raise NotImplementedError
        
        
    def remove(self, owner):
        raise NotImplementedError
        
        
    def get_field(self):
        raise NotImplementedError
    
    
class Many(Relationship):
    
    def __init__(self, model, field=None, *args, **kwargs):
        super(Many, self).__init__(model, *args, **kwargs)
        
        if self.instance_class is None:
            self.instance_class = ManyInstance
            
        if field is None:
            self.field = self.get_default_field_name()
        else:
            self.field = field
            
            
    def get(self, owner):
        if self.embedded:
            return [self.get_model()(**fields) for fields in owner._fields.get(self.field, [])]
            
        return self.instance_class(
            self,
            owner
        )
    
    def remove(self, owner):
        if self.cascade and not self.embedded:
            self.get_model().get_collection().remove({ self.field: owner._id })
    
    
class ManyInstance(object):
    
    def __init__(self, relationship, owner):
        self.relationship = relationship
        self.owner = owner
        
    def find_one(self, spec_or_id=None, *args, **kwargs):
        q = { self.relationship.field: self.owner._id }
        
        if isinstance(spec_or_id, ObjectId):
            q['_id'] = spec_or_id
        elif spec_or_id is not None:
            q.update(spec_or_id)
        
        fields = self.relationship.model.get_collection().find_one(q, *args, **kwargs)
        
        if fields:
            return self.relationship.get_model()(**fields)
        
        
    def find(self, spec=None, *args, **kwargs):
        q = { self.relationship.field: self.owner._id }
        
        if spec is not None:
            q.update(spec)
        
        return CursorProxy(self.relationship.get_model(), 
            self.relationship.get_model().get_collection().find(q, *args, **kwargs))
        
        
    def add(self, obj):
        assert isinstance(obj, self.relationship.get_model()), "Expected a '%s' object" % self.relationship.get_model().__name__
        obj._fields[self.relationship.field] = self.owner._id
        obj.save()
    
    
class One(Relationship):
    
    def __init__(self, model, field=None, *args, **kwargs):
        super(One, self).__init__(model, *args, **kwargs)
        
        if field is None:
            self.field = self.get_default_field_name()
        else:
            self.field = field
            
            
    def get(self, owner):
        if id:
            if self.embedded:
                fields = owner._fields.get(self.field)
            else:
                id = owner._fields.get(self.field)
                fields = self.get_model().get_collection().find_one({'_id': id})
                
            if fields:
                return self.get_model()(**fields)
            
            
    def set(self, owner, obj):
        assert isinstance(obj, self.get_model()), "Expected a '%s' object" % self.get_model().__name__
        
        if obj is None:
            owner._fields.pop(self.field)
        
        if self._embedded:
            owner._fields[self.field] = obj._fields
            obj.embedded = True
        else:
            assert '_id' in obj._fields, "Trying to add an unsaved '%s' object to a relationship" % self.get_model().__name__
            owner._fields[self.field] = obj._id
        
        return obj
        
        
    def remove(self, owner):
        if not self.cascade:
            return
        
        if not self.embedded:
            id = owner._fields.get(self.field)
            if id and self.cascade:
                self.get_model().get_collection().remove({ '_id': id })
                
                
                
class CursorProxy(object):
    
    def __init__(self, model, cursor):
        self._model = model
        self._cursor = cursor
        
        
    def __getitem__(self, index):
        return model(self._cursor.__getitem__(index))
        
        
    def __getattr__(self, name):
        return getattr(self._cursor, name)
        
        
    def next(self):
        return model(self._cursor.next())
