import registry
import connection
from cursor import CursorProxy


class Relationship(object):
    
    def __init__(self, target_model, inverse=None, cascade=False):
        """Create a relationship between two models.
        
        :param target_model: The model type that is the target of the relationship.
        :param inverse: The name of the inverse relationsip on the target. This relationship will be created automatically and does not need to be defined on the target.
        :param cascade: If ``True``, when an instance is removed, the related target models will also be removed.
        """
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
            target_model = self.get_target_model()
            owner_name = self._owner_cls.get_full_name()
            # This relationship was specified as a backreference in an earlier definition
            if owner_name in registry.back_references and self._name in registry.back_references[owner_name]:
                self.set_inverse(registry.back_references[owner_name][self._name])
            # The target already has an inverse relationship defined
            elif hasattr(target_model, self._inverse_name):
                inverse_rel = getattr(target_model, self._inverse_name)
                if inverse_rel._inverse:
                    raise AssertionError, "Attempt to redefine inverse relationship %s.%s" % (target_model.get_full_name(), self._inverse_name)
                else:
                    inverse_rel.set_inverse(self)
            else:
                setattr(target_model, self._inverse_name, self.inverse())
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
            self._inverse._target_model = self._owner_cls
            self._inverse._owner_cls = self.get_target_model()
            self._inverse._inverse_name = self._name
            self._inverse._inverse = self
            self._inverse._name = self._inverse_name
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
        
        
    def get_spec_from_target_or_spec(self, owner, target_or_spec):
        if isinstance(target_or_spec, self.get_target_model()):
            target_or_spec.assert_saved()
            spec = {'_id':target_or_spec._id}
        else:
            spec = self.spec(owner)
            if target_or_spec:
                target_or_spec.update(spec)
                spec = target_or_spec
        return spec
        
        
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
        if spec:
            spec.update(self.spec(owner))
        else:
            spec = self.spec(owner)
        return self.get_target_model().find(spec)
        
        
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
        spec = self.get_spec_from_target_or_spec(owner, target_or_spec)
        self.get_target_model().get_collection().update(
            spec,
            {'$unset':{self._inverse_name:True}},
            multi=True
        )
        
        
    def count(self, owner, spec=None):
        return self.find(owner, spec).count()
        
        
    def cascade(self, owner):
        if owner._id:
            self.get_target_model().remove(self.spec(owner))

    
class ManyToMany(Many):
    
    class StoragePolicy(object):
        
        def add(self, rel, owner, target):
            raise NotImplementedError
        
        def remove(self, rel, owner, target):
            raise NotImplementedError
            
        def spec(self, rel, owner):
            raise NotImplementedError
            
        def inverse(self):
            raise NotImplementedError
            
        def validate_inverse(self, policy):
            raise NotImplementedError
            
        def count(self, rel, owner, spec):
            if spec:
                spec.update(self.spec(rel, owner))
            else:
                spec = self.spec()
                
            return rel.get_target_model().get_collection().find(spec).count()
    
    
    class List(StoragePolicy):
        
        def _list_add(self, reference_field, owner, target):
            if not owner._reference_fields.get(reference_field):
                owner._reference_fields[reference_field] = []
            elif target._id in owner._reference_fields[reference_field]:
                return
            for obj in registry.get_model_instances(owner._id):
                if not obj._reference_fields.get(reference_field):
                    obj._reference_fields[reference_field] = []
                obj._reference_fields[reference_field].append(target._id)
            owner.get_collection().update(
                {'_id':owner._id},
                {'$addToSet':{reference_field:target._id}}
            )
    
    
    class LocalList(List):
        
        def add(self, rel, owner, target):
            self._list_add(rel._name, owner, target)
            
            
        def remove(self, rel, owner, target_ids):
            filtered_ids = filter(lambda x: x not in target_ids, owner._reference_fields[rel._name])
            
            for obj in registry.get_model_instances(owner._id):
                obj._reference_fields[rel._name] = filtered_ids
            
            owner.get_collection().update(
                {'_id':owner._id},
                {'$pullAll':{rel._name:target_ids}}
            )
            
            
        def count(self, rel, owner, spec):
            if spec:
                return super(ManyToMany.LocalList, self).count(rel, owner, spec)
                
            ids = owner._reference_fields.get(rel._name)
            if ids:
                return len(ids)
            else:
                return 0
            
            
        def spec(self, rel, owner):
            return {'_id':{'$in':owner._reference_fields.get(rel._name, [])}}
            
            
        def inverse(self):
            return ManyToMany.RemoteList()
            
            
        def validate_inverse(self, policy):
            assert isinstance(policy, ManyToMany.RemoteList), "Expected ManyToMany.RemoteList got %s" % policy.__class__.__name__
        
        
    class RemoteList(List):
        
        def add(self, rel, owner, target):
            self._list_add(rel._inverse_name, target, owner)
            
                
        def remove(self, rel, owner, target_ids):
            for target_id in target_ids:
                for obj in registry.get_model_instances(target_id):
                    try:
                        obj._reference_fields[rel._inverse_name].remove(owner._id)
                    except ValueError:
                        pass
            
            rel.get_target_model().get_collection().update(
                {'_id':{'$in':target_ids}},
                {'$pull':{rel._inverse_name:owner._id}},
                multi=True
            )
            
            
        def count(self, rel, owner, spec):
            if spec:
                return super(ManyToMany.RemoteList, self).count(rel, owner, spec)
                
            return rel.get_target_model().get_collection().find(self.spec(rel, owner)).count()
            
            
        def spec(self, rel, owner):
            return {rel._inverse_name:owner._id}
            
            
        def inverse(self):
            return ManyToMany.LocalList()
            
            
        def validate_inverse(self, policy):
            assert isinstance(policy, ManyToMany.LocalList), "Expected ManyToMany.LocalList got %s" % policy.__class__.__name__
        
        
    class LocalAndRemoteList(LocalList):
        
        def add(self, rel, owner, target):
            self._list_add(rel._name, owner, target)
            self._list_add(rel._inverse_name, target, owner)
            
            
        def remove(self, rel, owner, target_ids):
            super(ManyToMany.LocalAndRemoteList, self).remove(rel, owner, target_ids)
            
            for target_id in target_ids:
                for obj in registry.get_model_instances(target_id):
                    field = obj._reference_fields.get(rel._inverse_name)
                    if field:
                        try:
                            field.remove(owner._id)
                        except ValueError:
                            pass
            
            rel.get_target_model().get_collection().update(
                {'_id':{'$in':target_ids}},
                {'$pull':{rel._inverse_name:owner._id}},
                multi=True
            )
            
            
        def inverse(self):
            return ManyToMany.LocalAndRemoteList()
            
            
        def validate_inverse(self, policy):
            assert isinstance(policy, ManyToMany.LocalAndRemoteList), "Expected ManyToMany.LocalAndRemoteList got %s" % policy.__class__.__name__
        
        
    class Join(StoragePolicy):
        
        def __init__(self, join=None):
            self._join = join
            self._join_collection = None
        
        
        def add(self, rel, owner, target):
            owner_key, target_key, join_collection = self.get_join_context(rel, owner)
            entry = {
                owner_key: owner._id,
                target_key: target._id
            }
            join_collection.update(
                entry,
                {'$set': entry},
                upsert=True
            )
            
            
        def remove(self, rel, owner, target_ids):
            owner_key, target_key, join_collection = self.get_join_context(rel, owner)
            join_collection.remove({
                owner_key: owner._id,
                target_key: {'$in':target_ids}
            })
            
            
        def count(self, rel, owner, spec):
            if spec:
                return super(ManyToMany.Join, self).count(rel, owner, spec)
                
            owner_key, target_key, join_collection = self.get_join_context(rel, owner)
            return join_collection.find({owner_key:owner._id}).count()
            
            
        def spec(self, rel, owner):
            owner_key, target_key, join_collection = self.get_join_context(rel, owner)
            ids = [r[target_key] for r in join_collection.find({owner_key:owner._id}, fields=[target_key])]
            return {
                '_id':{
                    '$in': ids
                }
            }
            
            
        def get_join_context(self, rel, owner):
            if not self._join:
                return None, None, None
            if not self._join_collection:
                self._owner_key = owner.__class__.__name__
                self._target_key = rel.get_target_model().__name__
                self._join_collection = connection.database[self._join]
                self._join_collection.ensure_index([
                    (self._owner_key, 1),
                    (self._target_key, 1)
                ])
            return self._owner_key, self._target_key, self._join_collection
            
            
        def inverse(self):
            return ManyToMany.Join(self._join)
            
            
        def validate_inverse(self, policy):
            assert isinstance(policy, ManyToMany.Join), "Expected ManyToMany.Join got %s" % policy.__class__.__name__
    
    
    def __init__(self, target_model, inverse=None, cascade=False, storage_policy=LocalList):
        super(ManyToMany, self).__init__(target_model, inverse=inverse, cascade=cascade)
        
        if isinstance(storage_policy, ManyToMany.StoragePolicy):
            self._storage_policy = storage_policy
        elif isinstance(storage_policy, type):
            self._storage_policy = storage_policy()
        else:
            self._storage_policy = None
            
        
    def create_inverse(self):
        rel = ManyToMany(self._owner_cls)
        rel._storage_policy = self._storage_policy.inverse()
        return rel
        
        
    def validate_inverse(self, rel):
        super(ManyToMany, self).validate_inverse(rel)
        assert isinstance(rel, ManyToMany), "Expected ManyToMany got %s" % rel.__class__.__name__
        self._storage_policy.validate_inverse(rel._storage_policy)
        
        
    def add(self, owner, target):
        owner.assert_saved()
        target.assert_saved()
        self._storage_policy.add(self, owner, target)
        
        
    def remove(self, owner, target_or_spec=None):
        target_ids = self.get_target_ids(owner, target_or_spec)
        if len(target_ids) == 0:
            return
        self._storage_policy.remove(self, owner, target_ids)
        
        
    def get_target_ids(self, owner, target_or_spec):
        spec = self.get_spec_from_target_or_spec(owner, target_or_spec)
        target_collection = self.get_target_model().get_collection()
        return [r['_id'] for r in target_collection.find(spec, [])]
        
        
    def cascade(self, owner):
        spec = self.spec(owner)
        self.get_target_model().remove(spec)
        
        
    def spec(self, owner):
        return self._storage_policy.spec(self, owner)
        
        
    def count(self, owner, spec=None):
        return self._storage_policy.count(self, owner, spec)
        