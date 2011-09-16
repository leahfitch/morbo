from validators import Validator, InvalidError, InvalidGroupError
from relationships import Relationship, CursorProxy
import connection


class ModelMeta(type):
    
    def __new__(cls, name, bases, attrs):
        newattrs = {
            '_validators': {},
            '_relationships': {},
            '_fields': {}
        }
        
        for k,v in attrs.items():
            if isinstance(v, Validator):
                newattrs['_validators'][k] = v
                newattrs['_fields'][k] = None
            elif isinstance(v, Relationship):
                newattrs['_relationships'][k] = v
            else:
                newattrs[k] = v
        
        if 'collection_name' not in newattrs:
            n = name.lower()
            newattrs['collection_name'] = n + 'es' if n[-1] == 's' else n + 's'
        
        return type.__new__(cls, name, bases, newattrs)



class Model(object):
    __metaclass__ = ModelMeta
    _collection = None
    
    @classmethod
    def get_collection(cls):
        if cls._collection is None:
            cls._collection = connection.database[cls.collection_name]
        return cls._collection
        
        
    @classmethod
    def find(cls, spec=None, *args, **kwargs):
        return CursorProxy(cls, cls.get_collection().find(spec, *args, **kwargs))
        
        
    @classmethod
    def find_one(cls, spec_or_id=None, *args, **kwargs):
        fields = cls.get_collection().find_one(spec_or_id, *args, **kwargs)
        if fields:
            return cls(**fields)
    
    
    def __init__(self, **kwargs):
        parent = super(Model, self)
        parent.__setattr__('_related_instances', {})
        parent.__setattr__('_fields', kwargs)
        parent.__setattr__('embedded', False)
    
    
    def __getattr__(self, name):
        try:
            if name not in self._related_instances:
                r = self._relationships[name]
                self._related_instances[name] = r.get(self)
            return self._related_instances[name]
        except KeyError:
            try:
                return self._fields[name]
            except KeyError:
                return super(Model, self).__getattribute__(name)
    
    
    def __setattr__(self, name, value):
        try:
            r = self._relationships[name]
            self._related_instances[name] = r.set(self, value)
        except KeyError:
            if name in self._validators:
                self._fields[name] = value
            else:
                super(Model, self).__setattr__(name, value)
    
    
    def validate(self):
        errors = {}
        for k,v in self._validators.items():
            if not v.optional and k not in self._fields:
                errors[k] = 'This field is required.'
            elif k in self._fields:
                try:
                    self._fields[k] = v.validate(self._fields[k])
                except InvalidError, ve:
                    errors[k] = ve.message
        
        if errors:
            raise CompoundInvalidError(errors)
    
    
    def save(self):
        assert not self.embedded, "Attempting to save embedded '%s' object." % self.__class__.__name__
        self.validate()
        self.get_collection().save(self._fields)
        
        
    def remove(self):
        assert not self.embedded, "Attempting to delete an embedded '%s' object." % self.__class__.__name__
        assert '_id' in self._fields, "Attempting to remove unsaved '%s' object." % self.__class__.__name__
        
        for r in self._relationships.values():
            r.remove(self)
            
        self._related_instances = {}
        
        self.get_collection().remove({ '_id': self._id })
        self._fields.pop('_id')
