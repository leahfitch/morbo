"""
Models are classes whose instances persist in a MongoDB database. Other than the
special validator fields, Models are just regular python classes.
You can have whatever non-validator attributes and methods you want.
Along with simple persistence, Model subclasses also provide methods for finding,
removing and updating instances using almost the same API as pymongo.
"""
from validators import Validator, InvalidError, InvalidGroupError
from cursor import CursorProxy
from relationships import Relationship
import connection
import registry

__all__ = ['Model']

class ModelMeta(type):
    def __init__(cls, name, bases, dict):
        super(ModelMeta, cls).__init__(name, bases, dict)
        
        full_name = cls.get_full_name()
        registry.models[full_name] = cls
        
        # _ib is for "inheritance bases" and _it is for "inheritance type"
        _ib = []
        
        for b in bases:
            if hasattr(b, '__metaclass__') and b.__metaclass__ == ModelMeta and b != Model:
                setattr(cls, 'collection_name', b.collection_name)
                _ib.append(b.get_full_name())
        
        if len(_ib) > 0:
            cls._it = full_name
            _ib.append(cls._it)
            cls._ib = _ib
        elif 'collection_name' not in dict:
            setattr(cls, 'collection_name', name.lower())
        
        for k,v in dict.items():
            if isinstance(v, (Relationship,)):
                v.setup(k, cls)
                
        if 'indexes' in dict:
            col = cls.get_collection()
            for key_or_list in dict['indexes']:
                col.ensure_index(key_or_list)
        
        if full_name in registry.back_references:
            for name, inverse_rel in registry.back_references[full_name].items():
                rel = inverse_rel.inverse()
                setattr(cls, name, rel)
                rel.setup(name, cls)


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
    collection_name = None
    _collection = None
    _ib = None
    _it = None
    
    @classmethod
    def get_full_name(cls):
        return "%s.%s" % (cls.__module__, cls.__name__)
    
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
        spec = cls._spec_from_spec_or_id(spec)
        return CursorProxy(cls, cls.get_collection().find(spec, *args, **kwargs))
        
        
    @classmethod
    def find_one(cls, spec_or_id=None, *args, **kwargs):
        """
        Just like pymongo.Collection.find_one() but returns an instance of this
        model.
        """
        spec = cls._spec_from_spec_or_id(spec_or_id)
        fields = cls.get_collection().find_one(spec, *args, **kwargs)
        if fields:
            return cls(**fields)
    
    
    @classmethod
    def count(cls):
        """
        Get a count of the total number of instances of this model.
        """
        if cls._it:
            return cls.get_collection().find({'_ib':cls._it}).count()
        else:
            return cls.get_collection().count()
        
        
    @classmethod
    def remove(cls, spec=None):
        """
        Works just like pymongo.Collection.remove(). Note that this is different than the model instance
        method remove() which removes just that single instance.
        """
        spec = cls._spec_from_spec_or_id(spec)
        cascading_relationships = 0
        for k,v in cls.__dict__.items():
            if isinstance(v, Relationship) and v._cascade:
                cascading_relationships += 1
        if cascading_relationships > 0:
            for m in cls.find(spec):
                m.remove()
        else:
            cls.get_collection().remove(spec)
    
    
    @classmethod
    def _spec_from_spec_or_id(cls, spec_or_id):
        if not spec_or_id:
            spec_or_id = {}
        if not isinstance(spec_or_id, dict):
            spec_or_id = {'_id':spec_or_id}
        if cls._it:
            spec_or_id['_ib'] = cls._it
        return spec_or_id
    
    
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
        self._reference_fields = {}
        for k,v in self.__class__.__dict__.items():
            if isinstance(v, Validator):
                setattr(self, k, kwargs.get(k))
            elif isinstance(v, Relationship):
                self._reference_fields[k] = kwargs.get(k)
        setattr(self, '_id', kwargs.get('_id'))
        self.remove = self._remove
        
        if self._id:
            registry.add_model_instance(self)
    
    
    def __str__(self):
        return "<%s \"%s\">" % (
            self.__class__.__name__,
            self._id if self._id else "unsaved"
        )
        
        
    def __repr__(self):
        return str(self)
        
        
    def __eq__(self, other):
        """
        Compare this model instance with another one. They are equal if they 
        have the same _id.
        """
        if not isinstance(other, Model) or self._id is None or other._id is None:
            return False
        return self._id == other._id
    
    
    def validate(self):
        """
        Run validation on all validated fields.
        """
        errors = {}
        d = {}
        for k,v in self.__class__.__dict__.items():
            if isinstance(v, Validator):
                if not v.optional and getattr(self, k) is None:
                    errors[k] = 'This field is required.'
                elif getattr(self, k) is not None:
                    try:
                        d[k] = v.validate(getattr(self, k))
                    except InvalidError, ve:
                        errors[k] = ve.message
                    else:
                        setattr(self, k, d[k])
        if errors:
            raise InvalidGroupError(errors)
        
        
        for k in ['_id', '_ib']:
            if hasattr(self, k):
                v = getattr(self, k)
                if v:
                    d[k] = v
            
        return d
    
    
    def save(self):
        """
        Save this instance to the database. Validation is performed first.
        """
        d = self.validate()
        self.get_collection().save(d)
        if not self._id:
            self._id = d['_id']
            registry.add_model_instance(self)
            self.was_created()
        else:
            self.was_modified()
            
            
    def assert_saved(self):
        assert self._id is not None, "Expected a saved model (i.e., one with an id)."
        
        
    def was_created(self):
        """
        Called after the model is saved for the first time.
        """
        
        
    def was_modified(self):
        """
        Called each time the model is saved after the first save.
        """
        
        
    def _remove(self):
        """
        Remove this instance from the database.
        """
        assert self._id is not None, "Attempting to remove unsaved '%s' object." % self.__class__.__name__
        
        for k,v in self.__class__.__dict__.items():
            if isinstance(v, Relationship):
                v.on_owner_remove(self)
        
        self.get_collection().remove({ '_id': self._id })
        self._id = None
