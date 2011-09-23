"""
Models are classes whose instances persist in a MongoDB database. Other than the
special validator and relationship fields, Models are just regular python classes.
You can have whatever non-validator/relationship attributes and methods you want.
Along with simple persistence, Model subclasses also provide methods for finding,
removing and updating instances using almost the same API as pymongo.
"""
from validators import Validator, InvalidError, InvalidGroupError
from relationships import Relationship
from cursor import CursorProxy
import connection


class ModelMeta(type):
    """
    Creates new Model types. Cool.
    """
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
    """
    A class with persistent instances::
    
        class Swallow(Model):
            is_laden = Bool()
            speed = TypeOf(float)
            direction = Enum('N', 'E', 'S', 'W')
            
        s = Swallow(is_laden=True, speed=23.7, direction='E')
        s.save()
        repr(s._id) # ObjectId('4e7be644d761504a98000000')
    """
    __metaclass__ = ModelMeta
    _collection = None
    
    @classmethod
    def get_collection(cls):
        """
        Get a pymongo.Collection instance for the collection that backs instances
        of this model::
            
            class Swallow(Model):
                ...
            
            Swallow.get_collection() # Collection(Database(Connection('localhost', 27017), u'morbotests'), u'test')
        """
        if cls._collection is None:
            cls._collection = connection.database[cls.collection_name]
        return cls._collection
        
        
    @classmethod
    def find(cls, spec=None, *args, **kwargs):
        """
        Find instances of this model. This method is exactly the same as 
        pymongo.Collection.find() except that the returned cursor returns instances
        of this model instead of dicts::
            
            class Swallow(Model):
                ...
            
            s = Swallow(is_laden=True, speed=23.7, direction='E')
            s.save()
            
            Swallow.find({'direction':'E'}).next() # <Swallow 4e7bea8fd761504ae3000000>
        """
        return CursorProxy(cls, cls.get_collection().find(spec, *args, **kwargs))
        
        
    @classmethod
    def find_one(cls, spec_or_id=None, *args, **kwargs):
        """
        Just like pymongo.Collection.find_one() but returns an instance of this
        model.
        """
        fields = cls.get_collection().find_one(spec_or_id, *args, **kwargs)
        if fields:
            return cls(**fields)
    
    
    @classmethod
    def count(cls):
        """
        Get a count of the total number of instances of this model.
        """
        return cls.get_collection().count()
        
        
    @classmethod
    def find_and_remove(cls, spec=None):
        """
        Works just like pymongo.Collection.remove(). It has a different name
        so as not to conflict with the instance method remove().
        """
        cls.get_collection().remove(spec)
    
    
    def __init__(self, **kwargs):
        """
        Create a new instance of a model optionally setting any of its fields::
        
            class Swallow(Model):
                is_laden = Bool()
                speed = TypeOf(float)
                direction = Enum('N', 'E', 'S', 'W')
            
            # Create a model and set all its fields
            s = Swallow(is_laden=True, speed=23.7, direction='E')
            
            # Create a model and then set some fields
            t = Swallow()
            t.is_laden = False
            
            # Validation doesn't occur until save
            t.save()
            # raises InvalidGroupError since this instance is missing two fields
            
            t.speed = 5
            t.direction = 'S'
            t.save() # ok, we are in the db now
            
        """
        parent = super(Model, self)
        parent.__setattr__('_related_instances', {})
        parent.__setattr__('_fields', kwargs)
        parent.__setattr__('embedded', False)
    
    
    def __str__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self._fields['_id'] if '_id' in self._fields else 'unsaved'
        )
        
        
    def __repr__(self):
        return str(self)
        
        
    def __eq__(self, other):
        """
        Compare this model instance with another one. They are equal if they 
        have the same _id.
        """
        if not isinstance(other, Model):
            return False
        return self._fields.get('_id', 0) == other._fields.get('_id', 1)
    
    
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
        """
        Run validation on all validated fields.
        """
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
            raise InvalidGroupError(errors)
    
    
    def save(self):
        """
        Save this instance to the database. Validation is performed first.
        """
        assert not self.embedded, "Attempting to save embedded '%s' object." % self.__class__.__name__
        self.validate()
        self.get_collection().save(self._fields)
        
        
    def remove(self):
        """
        Remove this instance from the database.
        """
        assert not self.embedded, "Attempting to delete an embedded '%s' object." % self.__class__.__name__
        assert '_id' in self._fields, "Attempting to remove unsaved '%s' object." % self.__class__.__name__
        
        for r in self._relationships.values():
            r.remove(self)
            
        self._related_instances = {}
        
        self.get_collection().remove({ '_id': self._id })
        self._fields.pop('_id')
