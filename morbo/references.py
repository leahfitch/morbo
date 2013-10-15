"""
References are links between models. There are two types: `One` and `Many`.
Each type can use a number of different storage policies. These policies
define the structure of a link and are responsible for actually fetching data.
Writing custom storage policies is supported and encouraged.
"""
from bson.objectid import ObjectId
import importlib
from cursor import CursorProxy
import connection

__all__ = ['Reference', 'One', 'Many', 'Remote', 'Local', 'Join']


class Reference(object):
    """
    Base class for references.
    """
    
    def __init__(self, model, storage_policy, cascade=False):
        """
        Create a new reference to `model` using `storage_policy`. If `cascade`
        is `True` then the referenced model(s) will be removed when the owner
        of this reference is removed.
        """
        self.model = model
        self.cascade = cascade
        self.name = None
        
        if isinstance(storage_policy, (type,)):
            self.storage_policy = storage_policy()
        else:
            self.storage_policy = storage_policy
    
    
    def get_model(self):
        if isinstance(self.model, basestring):
            parts = self.model.split('.')
            n = parts.pop()
            m = importlib.import_module('.'.join(parts))
            self.model = getattr(m, n)
        return self.model
        
        
    def get_model_name(self):
        if isinstance(self.model, basestring):
            return self.model
        else:
            return self.model.__name__
    
    
    def setup_with_owner(self, owner_model, name):
        self.name = name
        self.storage_policy.setup_with_reference(self, owner_model.__name__, self.get_model_name())
        
        
    def setup_reference_fields(self, owner, doc):
        for k,v in self.storage_policy.get_owner_reference_fields(self, owner).items():
            owner._reference_fields[k] = doc.get(k, v)
        
        
    def cascading_remove(self, owner):
        if self.cascade:
            self.storage_policy.cascade(self, owner, self.get_model())
        
        
        
class One(Reference):
    """
    A reference to a single, lazy-loaded model.
    """
    def __get__(self, owner, cls):
        return self.storage_policy.get_one(self, owner, self.get_model())
        
        
    def __set__(self, owner, target):
        if target == None:
            self.__delete__(owner)
        else:
            self.storage_policy.set_one(self, owner, target)
        
        
    def __delete__(self, owner):
        target = self.__get__(owner, owner.__class__)
        if target:
            self.storage_policy.remove_one(self, owner, target)
        
        
        
class Many(Reference):
    """
    Reference to a group of models.
    """
    
    def __get__(self, owner, cls):
        return ManyProxy(self, owner)
        
    
    def find(self, owner, spec=None):
        return self.storage_policy.get_list(self, owner, self.get_model(), spec)
        
        
    def add(self, owner, target):
        self.storage_policy.add_to_list(self, owner, target)
        
        
    def remove(self, owner, target):
        self.storage_policy.remove_from_list(self, owner, target)
        
        
class ManyProxy(object):
    """Proxies calls to a Many reference, passing on a predefined owner"""
    
    def __init__(self, reference, owner):
        self.reference = reference
        self.owner = owner
        
    def find(self, spec=None):
        return self.reference.find(self.owner, spec)
        
    def add(self, target):
        return self.reference.add(self.owner, target)
        
    def remove(self, target):
        return self.reference.remove(self.owner, target)


class StoragePolicy(object):
    """
    This is the abstract base class for all storage policies.
    """
    
    def setup_with_reference(self, reference, owner_name, target_name):
        """
        Perform any setup that needs to occur once we have access to the reference instance
        and the owner and target model names.
        """
        pass
        
        
    def get_owner_reference_fields(self, reference, owner):
        """Return a dict of field_name => default_value for fields the owner must have
        for this storage policy to work."""
        return {}
        
        
    def get_one(self, reference, owner, model):
        """
        Get a single model.
        """
        raise NotImplementedError
        
        
    def set_one(self, reference, owner, target):
        """
        Set a single model.
        """
        raise NotImplementedError
        
        
    def remove_one(self, reference, owner):
        """
        Remove a single model.
        """
        raise NotImplementedError
        
        
    def get_list(self, reference, owner, model, spec=None):
        """
        Get a model cursor.
        """
        raise NotImplementedError
        
        
    def add_to_list(self, reference, owner, target):
        """
        Add one model to a group
        """
        raise NotImplementedError
        
        
    def remove_from_list(self, reference, owner, target):
        """
        Remove one model from a group
        """
        raise NotImplementedError
        
        
    def cascade(self, reference, owner, model):
        "Remove all the associated models (not just their links)"
        raise NotImplementedError
        
        
        
class Remote(StoragePolicy):
    """
    Reference models by storing the owner's id in a field on the target.
    """
    
    def __init__(self, id_field=None):
        self.id_field = id_field
        
    
    def setup_with_reference(self, reference, owner_name, target_name):
        if not self.id_field:
            self.id_field = owner_name + '_id'
                    
        
    def get_one(self, reference, owner, model):
        doc = model.get_collection().find_one(
            {
                self.id_field: owner._id
            })
        
        if not doc:
            return None
        
        return model(**doc)
        
        
    def set_one(self, reference, owner, target):
        target.get_collection().update(
            { self.id_field: owner._id },
            { '$unset': { self.id_field: True } }
        )
        target.get_collection().update(
            { '_id': target._id },
            { '$set': { self.id_field: owner._id } }
        )
        
        
    def remove_one(self, reference, owner, target):
        target.get_collection().update(
            { '_id': target._id },
            { '$unset': { self.id_field: True } }
        )
        
        
    def get_list(self, reference, owner, model, spec=None):
        if spec is None:
            spec = {}
        spec[self.id_field] = owner._id
        return CursorProxy(model, model.get_collection().find(spec))
        
        
    def add_to_list(self, reference, owner, target):
        target.get_collection().update(
            { '_id': target._id },
            { '$set': { self.id_field: owner._id } }
        )
        
        
    def remove_from_list(self, reference, owner, target):
        self.remove_one(reference, owner, target)
        
        
    def cascade(self, reference, owner, model):
        model.remove({
            self.id_field: owner._id
        })


class Local(StoragePolicy):
    """Reference a model(s) using a local field"""
    
    def __init__(self, id_field=None):
        self.id_field = id_field
        
        
    def setup_with_reference(self, reference, owner_name, target_name):
        if not self.id_field:
            self.id_field = reference.name
        
        
    def get_owner_reference_fields(self, reference, owner):
        return { self.id_field: ([] if isinstance(reference, (Many,)) else None) }
        
    
    def get_one(self, reference, owner, model):
        if not owner._reference_fields.get(self.id_field):
            return None
        
        return model.find_one(owner._reference_fields[self.id_field])
        
        
    def set_one(self, reference, owner, target):
        owner.get_collection().update(
            { '_id': owner._id },
            {
                '$set': { self.id_field: target._id }
            }
        )
        owner._reference_fields[self.id_field] = target._id
        
        
    def remove_one(self, reference, owner, target):
        owner.get_collection().update(
            { '_id': owner._id },
            {
                '$unset': { self.id_field: True }
            }
        )
        owner._reference_fields[self.id_field] = None
        
        
    def get_list(self, reference, owner, model, spec=None):
        if self.id_field not in owner._reference_fields:
            return CursorProxy(model, { '_id':None } )
        if spec is None:
            spec = {}
        spec['_id'] = { '$in': owner._reference_fields[self.id_field] }
        return CursorProxy(model, model.get_collection().find(spec))
        
        
    def add_to_list(self, reference, owner, target):
        if target._id in owner._reference_fields[self.id_field]:
            return
        owner.get_collection().update(
            { '_id': owner._id },
            { '$addToSet': { self.id_field: target._id } }
        )
        owner._reference_fields[self.id_field].append(target._id)
        
        
    def remove_from_list(self, reference, owner, target):
        if target._id not in owner._reference_fields[self.id_field]:
            return
        owner.get_collection().update(
            { '_id': owner._id },
            { '$pull': { self.id_field: target._id } }
        )
        owner._reference_fields[self.id_field].remove(target._id)
        
        
    def cascade(self, reference, owner, model):
        if isinstance(reference, (Many,)):
            model.remove({
                '_id': { '$in': owner._reference_fields[self.id_field] }
            })
        else:
            model.remove({
                '_id': owner._reference_fields[self.id_field]
            })


class Join(StoragePolicy):
    """
    Reference models using a join collection
    """
    
    def __init__(self, collection_name=None, owner_id_field=None, target_id_field=None):
        self.collection = None
        self.collection_name = collection_name
        self.owner_id_field = owner_id_field
        self.target_id_field = target_id_field
        
        
    def setup_with_reference(self, reference, owner_name, target_name):
        if not self.collection_name:
            model_names = sorted([owner_name, target_name])
            self.collection_name = model_names[0] + '_' + model_names[1]
        if not self.owner_id_field:
            self.owner_id_field = owner_name + '_id'
        if not self.target_id_field:
            self.target_id_field = target_name + '_id'
        
        
    def get_collection(self):
        if not self.collection:
            self.collection = connection.database[self.collection_name]
        return self.collection
        
        
    def get_one(self, reference, owner, model):
        join_doc = self.get_collection().find_one(
            {
                self.owner_id_field: owner._id
            })
        
        if not join_doc:
            return None
        
        doc = model.get_collection().find_one(join_doc[self.target_id_field])
        
        if not doc:
            return None
        
        return model(**doc)
        
        
    def set_one(self, reference, owner, target):
        self.get_collection().update(
            {
                self.owner_id_field: owner._id,
            },
            {
                '$set': {
                    self.target_id_field: target._id
                }
            },
            upsert=True
        )
        
        
    def remove_one(self, reference, owner, target):
        self.get_collection().remove(
            {
                self.owner_id_field: owner._id,
                self.target_id_field: target._id
            }
        )
        
        
    def get_list(self, reference, owner, model, spec=None):
        join_docs = self.get_collection().find(
                                    { self.owner_id_field: owner._id })
        
        if join_docs.count() == 0:
            return CursorProxy(model, join_docs)
        
        if spec is None:
            spec = {}
        
        spec['_id'] = {'$in': [doc[self.target_id_field] for doc in join_docs]}
        return CursorProxy(model, model.get_collection().find(spec))
        
        
    def add_to_list(self, reference, owner, target):
        self.get_collection().update(
            {
                self.owner_id_field: owner._id,
                self.target_id_field: target._id
            },
            {
                '$set': {}
            },
            upsert=True
        )
        
        
    def remove_from_list(self, reference, owner, target):
        self.remove_one(reference, owner, target)
        
        
    def cascade(self, reference, owner, model):
        ids = [d[self.target_id_field] for d in self.get_collection().find({self.owner_id_field:owner._id})]
        model.remove({'_id':{'$in':ids}})
        
