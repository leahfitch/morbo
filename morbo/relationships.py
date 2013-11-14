import registry
import connection
from cursor import CursorProxy


class Relationship(object):
    
    def __init__(self, target_model, inverse=None, cascade=False):
        self._target_model = target_model
        self._inverse_name = inverse
        self._name = None
        self._owner_cls = None
        self._inverse = None
        self._cascade = cascade
        
        
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
            self._inverse._inverse_name = self._name
        return self._inverse
        
        
    def validate_inverse(self, rel):
        inverse_rel = self.create_inverse()
        if rel.__class__ != inverse_rel.__class__:
            raise TypeError, "Expected %s to be of type %s" % (rel.get_name(), inverse_rel.__class__.__name__)
        if rel.get_target_model() != inverse_rel.get_target_model():
            raise TypeError, "Expected %s to have a target of type %s" % (rel.get_name(), inverse_rel.get_target_model_name())
        
        
    def create_inverse(self):
        raise NotImplementedError
        
        
    def on_owner_remove(self, owner):
        if self._cascade:
            self.cascade(owner)
        
        
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
        
        
    def cascade(self, owner):
        raise NotImplementedError



class One(Relationship):
    
    def __init__(self, target_model, inverse=None):
        if inverse is not None:
            raise TypeError, "One-type relationships don't have an inverse."
        super(One, self).__init__(target_model)
        
        
    def get(self, owner):
        if not hasattr(self, '_cache'):
            id = owner._reference_fields.get(self._name)
            if id:
                self._cache = self.get_target_model().find_one(id)
            else:
                self._cache = None
        return self._cache
        
        
    def set(self, owner, target, update_inverse=True):
        target.assert_saved()
        self._cache = target
        
        for obj in registry.get_model_instances(owner._id):
            obj._reference_fields[self._name] = target._id
            
        if owner._id:
            owner.get_collection().update(
                {'_id':owner._id},
                {'$set':{self._name:target._id}}
            )
        
        
    def cascade(self, owner):
        target = self.get(owner)
        if target:
            target.remove()

        
class OneToOne(One):
    
    def __init__(self, target_model, inverse=None, cascade=False):
        Relationship.__init__(self, target_model, inverse, cascade)
        
    def create_inverse(self):
        return OneToOne(self._owner_cls)
        
    def set(self, owner, target, update_inverse=True):
        One.set(self, owner, target)
        if update_inverse and self._inverse:
            self._inverse.set(target, owner, update_inverse=False)
            
            
class ManyToOne(One):
    
    def __init__(self, target_model, inverse=None):
        Relationship.__init__(self, target_model, inverse)
        
    
    def create_inverse(self):
        return OneToMany(self._owner_cls)


class ManyProxy(object):
    
    def __init__(self, rel, owner):
        self._rel = rel
        self._owner = owner
        
        
    def count(self, spec=None):
        return self._rel.count(self._owner, spec)
        
        
    def __iter__(self):
        return self.find().__iter__()
        
        
    def find_one(self, spec_or_id=None):
        return self._rel.find_one(self._owner, spec_or_id)
        
        
    def find(self, spec=None):
        return self._rel.find(self._owner, spec)
        
        
    def add(self, target):
        return self._rel.add(self._owner, target)
        
        
    def remove(self, target_or_spec=None):
        return self._rel.remove(self._owner, target_or_spec)
        


class Many(Relationship):
    
    def setup(self, name, owner_cls):
        if not self._inverse_name:
            self._inverse_name = owner_cls.__name__.lower()
        super(Many, self).setup(name, owner_cls)
    
    
    def get(self, owner):
        owner.assert_saved()
        return ManyProxy(self, owner)
        
        
    def cascade(self, owner):
        self.remove(owner)
        
    
    def spec(self, owner):
        raise NotImplementedError
        
        
    def get_spec_from_target_or_spec(self, target_or_spec):
        if isinstance(target_or_spec, self.get_target_model()):
            target_or_spec.assert_saved()
            spec = {'_id':target_or_spec._id}
        else:
            spec = self.spec()
            if target_or_spec:
                target_or_spec.update(spec)
                spec = target_or_spec
        return spec
        
        
    def count(self, owner, spec=None):
        return self.find(owner, spec).count()
        
        
    def find_one(self, owner, spec_or_id=None):
        spec = self.spec(owner)
        if spec_or_id:
            if isinstance(spec_or_id, dict):
                spec_or_id.update(spec)
                spec = spec_or_id
            else:
                spec['_id'] = spec_or_id
                
        return self.get_target_model().find_one(spec)
        
        
    def find(self, owner, spec=None):
        _spec = self.spec(owner)
        if spec:
            spec.update(_spec)
            _spec = spec
        return self.get_target_model().find(_spec)
        
        
    def add(self, owner, target):
        raise NotImplementedError
        
        
    def remove(self, owner, target_or_spec=None):
        raise NotImplementedError
        
        
    
class OneToMany(Many):
    
    def create_inverse(self):
        return ManyToOne(self._owner_cls)
        
        
    def spec(self, owner):
        return { self._inverse_name:owner._id }
        
        
    def add(self, owner, target):
        owner.assert_saved()
        target.assert_saved()
        target.get_collection().update(
            {'_id':target._id},
            {'$set':{self._inverse_name:owner._id}}
        )
        
        
    def remove(self, owner, target_or_spec=None):
        spec = self.get_spec_from_target_or_spec(target_or_spec)
        self.get_target_model().get_collection().update(
            spec,
            {'$unset':{self._inverse_name:True}}
        )
        
        
    def cascade(self, owner):
        if owner._id:
            self.get_target_model().remove(self.spec(owner))
    
    
class ManyToMany(Many):
    
    def __init__(self, target_model, inverse=None, cascade=False, join=None):
        super(ManyToMany, self).__init__(target_model, inverse=inverse, cascade=cascade)
        self._join = join
        self._join_collection = None
        
        
    def create_inverse(self):
        return ManyToMany(self._owner_cls, join=self._join)
        
        
    def validate_inverse(self, rel):
        super(ManyToMany, self).validate_inverse(rel)
        if not rel._join:
            rel._join = self._join
        elif rel._join != self._join:
            raise AssertionError, "%s and %s specify different join collections" % (self.get_name(), rel.get_name())
        
        
    def add(self, owner, target):
        owner.assert_saved()
        target.assert_saved()
        if self._join:
            self._add_join(owner, target)
        else:
            self._add_local(owner, target)
        
        
    def _add_join(self, owner, target):
        owner_key, target_key, join_collection = self.get_join_context(owner)
        entry = {
            owner_key: owner._id,
            target_key: target._id
        }
        join_collection.update(
            entry,
            {'$set': entry},
            upsert=True
        )
        
        
    def _add_local(self, owner, target):
        if not owner._reference_fields.get(self._name):
            owner._reference_fields[self._name] = []
        if target._id not in owner._reference_fields[self._name]:
            for obj in registry.get_model_instances(owner._id):
                obj._reference_fields[self._name].append(target._id)
            owner.get_collection().update(
                {'_id':owner._id},
                {'$addToSet':{self._name:target._id}}
            )
            target.get_collection().update(
                {'_id':target._id},
                {'$addToSet':{self._inverse_name:owner._id}}
            )
        
        
    def remove(self, owner, target_or_spec=None):
        target_ids = self.get_target_ids(target_or_spec)
        if len(target_ids) == 0:
            return
            
        if self._join:
            self._remove_join(owner, target_ids)
        else:
            self._remove_local(owner, target_ids)
            
            
    def _remove_join(self, owner, target_ids):
        owner_key, target_key, join_collection = self.get_join_context(owner)
        join_collection.remove({target_key:{'$in':target_ids}})
        
        
    def _remove_local(self, owner, target_ids):
        filtered_ids = filter(lambda x: x not in target_ids, owner._reference_fields[self._name])
        
        for obj in registry.get_model_instances(owner._id):
            obj._reference_fields[self._name] = filtered_ids
            
        owner.get_collection().update(
            {'_id':owner._id},
            {'$pullAll':{self._name:filtered_ids}}
        )
        
        for target_id in target_ids:
            for obj in registry.get_model_instances(target_id):
                field = obj._reference_fields[self._inverse_name]
                try:
                    field.remove(owner._id)
                except ValueError:
                    pass
        
        self.get_target_model().get_collection().update(
            {'_id':{'$in':target_ids}},
            {'$pull':{self._inverse_name:owner._id}}
        )
        
        
    def get_target_ids(self, target_or_spec):
        spec = self.get_spec_from_target_or_spec(target_or_spec)
        target_collection = self.get_target_model().get_collection()
        return [r['_id'] for r in target_collection.find(spec, [])]
        
        
    def cascade(self, owner):
        spec = self.spec(owner)
        self.get_target_model().remove(spec)
        
        
    def spec(self, owner):
        if self._join:
            owner_key, target_key, join_collection = self.get_join_context(owner)
            ids = [r[target_key] for r in join_collection.find({owner_key:owner._id}, fields=[target_key])]
        else:
            ids = owner._reference_fields.get(self._name, [])
        
        return {'_id':{'$in':ids}}
        
        
    def get_join_context(self, owner):
        if not self._join:
            return None, None, None
        if not self._join_collection:
            self._owner_key = owner.__class__.__name__
            self._target_key = self.get_target_model().__name__
            self._join_collection = connection.database[self._join]
            self._join_collection.ensure_index([
                (self._owner_key, 1),
                (self._target_key, 1)
            ])
        return self._owner_key, self._target_key, self._join_collection
            