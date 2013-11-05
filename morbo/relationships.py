import registry


class Relationship(object):
    
    def __init__(self, target_model, inverse=None):
        self._target_model = target_model
        self._inverse_name = inverse
        self._name = None
        self._owner_cls = None
        self._inverse = None
        self._cache = None
        
        
    def setup(self, name, owner_cls):
        self._name = name
        self._owner_cls = owner_cls
        self.resolve_backreferences()
        
        
    def resolve_backreferences(self):
        if not self._inverse_name:
            return
            
        if self.is_target_model_defined():
            if hasattr(self._target_model, self._inverse_name):
                getattr(self._target_model, self._inverse_name).set_inverse(self)
            else:
                setattr(self._target_model, self._inverse_name, self.create_inverse())
        else:
            target_name = self.get_target_model_name()
            if target_name not in registry.back_references:
                registry.back_references[target_name] = {}
            elif self._inverse_name in registry.back_references[target_name]:
                raise AssertionError, "Attempt to redefine inverse relationship %s.%s" % (target_name, self._inverse_name)
            registry.back_references[target_name][self._inverse_name] = self
        
        
    def set_inverse(self, ref):
        if not isinstance(ref, Relationship):
            raise TypeError, "Expected a Relationship instance."
        self.validate_inverse(ref)
        self._inverse = ref
        ref._inverse = self
        
        
    def inverse(self):
        if not self._inverse:
            self._inverse = self.create_inverse()
            self._inverse._inverse = self
        return self._inverse
            
            
    def create_inverse(self):
        raise NotImplementedError
        
        
    def validate_inverse(self, rel):
        inverse_rel = self.create_inverse()
        if rel.__class__ != inverse_rel.__class__:
            raise TypeError, "Expected %s to be of type %s" % (rel.get_name(), inverse_rel.__class__.__name__)
        if rel.get_target_model() != inverse_rel.get_target_model():
            raise TypeError, "Expected %s to have a target of type %s" % (rel.get_name(), inverse_rel.get_target_model_name())
        
        
    def is_target_model_defined(self):
        return not isinstance(self._target_model, basestring)
        
        
    def get_target_model_name(self):
        if self.is_target_model_defined():
            return '%s.%s' % (self._target_model.__module__, self._target_model.__name__)
        else:
            name = self._target_model
            if '.' not in name:
                name = '%s.%s' % (self._owner_cls.__module__, name)
            return name
        
        
    def get_target_model(self):
        if not self.is_target_model_defined():
            name = self.get_target_model_name()
            self._target_model = registry.models.get(name)
            assert self._target_model is not None, "Could not find a model called '%s'" % name
        return self._target_model
        
        
    def get_name(self):
        return "%s.%s.%s" % (self._owner_cls.__module__, self._owner_cls.__name__, self._name)
        
        
    def __get__(self, instance, cls):
        if instance:
            return self.get(instance)
        else:
            return self
            
            
    def __set__(self, instance, value):
        model = self.get_target_model()
        assert isinstance(value, model), "Expected an instance of %s" % model.__name__
        self.set(instance, value)
        
        
    def get(self, owner):
        raise NotImplementedError
        
        
    def set(self, owner, target, update_inverse=True):
        raise NotImplementedError



class One(Relationship):
    
    def __init__(self, target_model, inverse=None):
        if inverse is not None:
            raise TypeError, "One-type relationships don't have an inverse."
        super(One, self).__init__(target_model)
        
        
    def get(self, owner):
        if not self._cache:
            id = owner._reference_fields.get(self._name)
            if id:
                self._cache = self.get_target_model().find_one(id)
        return self._cache
        
        
    def set(self, owner, target, update_inverse=True):
        assert target._id, "Attempt to reference an unsaved %s" % self.get_target_model().__name__
        self._cache = target
        owner._reference_fields[self._name] = target._id

        
class OneToOne(One):
    
    def __init__(self, target_model, inverse=None):
        Relationship.__init__(self, target_model, inverse)
        
    def create_inverse(self):
        return OneToOne(self._owner_cls)
        
    def set(self, owner, target, update_inverse=True):
        One.set(self, owner, target)
        if update_inverse and self._inverse:
            self._inverse.set(target, owner, update_inverse=False)
    
    
class OneToMany(Relationship):
    pass
    
    
class ManyToOne(Relationship):
    pass
    
    
class ManyToMany(Relationship):
    pass