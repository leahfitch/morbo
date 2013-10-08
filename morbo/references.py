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
        self.storage_policy = storage_policy
        self.cascade = cascade    
    
        
    def get_model(self):
        if isinstance(self.model, basestring):
            parts = self.model.split('.')
            n = parts.pop()
            m = importlib.import_module('.'.join(parts))
            print m
            self.model = getattr(m, n)
        return self.model
        
        
    def update_owner_reference_fields(self, owner, doc):
        f = self.storage_policy.get_owner_reference_field(owner)
        if f:
            k,v = f
            owner._reference_fields[k] = doc.get(k, v)
        
        
    def update_target_reference_fields(self, target, doc):
        f = self.storage_policy.get_target_reference_field(target)
        if f:
            k,v = f
            target._reference_fields[k] = doc.get(k, v)
        
    def remove(self, owner):
        if self.cascade:
            self.storage_policy.cascade(owner, self.get_model())
        
        
        
class One(Reference):
    """
    A reference to a single, lazy-loaded model.
    """
    def __get__(self, owner, cls):
        return self.storage_policy.get_one(owner, self.get_model())
        
        
    def __set__(self, owner, target):
        if target == None:
            self.__delete__(owner)
        else:
            self.storage_policy.set_one(owner, target)
        
        
    def __delete__(self, owner):
        target = self.__get__(owner, owner.__class__)
        if target:
            self.storage_policy.remove_one(owner, target)
        
        
        
class Many(Reference):
    """
    Reference to a group of models.
    """
    def find(self, owner, spec=None):
        return self.storage_policy.get_many(
                                owner, self.get_model(), spec)
        
        
    def add(self, owner, target):
        self.storage_policy.add_to_many(owner, target)
        
        
    def remove(self, owner, target):
        self.storage_policy.remove_from_many(owner, target)



class StoragePolicy(object):
    """
    This is the abstract base class for all storage policies.
    """
    
    def get_owner_reference_field(self, owner):
        """
        Get a tuple of `(field_name, default_value)` for the field the owner
        model needs in order to maintain the reference. If the owner field
        doesn't need any, return `None`
        """
        return None
        
        
    def get_target_reference_field(self, target):
        """
        Get a tuple of `(field_name, default_value)` for the field the target
        model needs in order to maintain the reference. If the owner field
        doesn't need any, return `None`
        """
        return None
        
        
    def get_one(self, owner, model):
        """
        Get a single model.
        """
        raise NotImplementedError
        
        
    def set_one(self, owner, target):
        """
        Set a single model.
        """
        raise NotImplementedError
        
        
    def remove_one(self, owner):
        """
        Remove a single model.
        """
        raise NotImplementedError
        
        
    def get_many(self, owner, model, spec=None):
        """
        Get a model cursor.
        """
        raise NotImplementedError
        
        
    def add_to_many(self, owner, target):
        """
        Add one model to a group
        """
        raise NotImplementedError
        
        
    def remove_from_many(self, owner, target):
        """
        Remove one model from a group
        """
        raise NotImplementedError
        
    def cascade(self, owner, model):
        "Remove all the associated models (not just their links)"
        raise NotImplementedError
        
        
        
class Remote(StoragePolicy):
    """
    Reference models by storing the owner's id in a field.
    """
    
    def __init__(self, id_field):
        self.id_field = id_field
        
        
    def get_target_reference_field(self, owner):
        return self.id_field, None
        
        
    def get_one(self, owner, model):
        doc = model.get_collection().find_one(
            {
                self.id_field: owner._id
            })
        
        if not doc:
            return None
        
        return model(**doc)
        
        
    def set_one(self, owner, target):
        target.get_collection().update(
            { self.id_field: owner._id },
            { '$unset': { self.id_field: True } }
        )
        target.get_collection().update(
            { '_id':target._id },
            { '$set': { self.id_field: owner._id } }
        )
        target._reference_fields[self.id_field] = owner._id
        
        
    def remove_one(self, owner, target):
        target.get_collection().update(
            { '_id':target._id },
            { '$unset': { self.id_field: True } }
        )
        target._reference_fields[self.id_field] = None
        
        
    def get_many(self, owner, model, spec=None):
        if spec is None:
            spec = {}
        spec[self.id_field] = owner._id
        return CursorProxy(model, model.get_collection().find(spec))
        
        
    def add_to_many(self, owner, target):
        self.set_one(owner, target)
        
        
    def remove_from_many(self, owner, target):
        self.remove_one(owner, target)
        
    def cascade(self, owner, model):
        model.get_collection().remove({
            self.id_field: owner._id
        })
        
        
        
class RemoteList(Remote):
    """
    Reference models by storing the owner's id in a list field with other ids.
    """
    
    def get_target_reference_field(self, target):
        return self.id_field, []
        
        
    def set_one(self, owner, target):
        if owner._id in target.reference_fields[self.id_field]:
            return
            
        target.get_collection().update(
            {'_id':target._id},
            {
                '$addToSet': { self.id_field: owner._id }
            }
        )
        target._reference_fields[self.id_field].append(owner._id)
        
        
    def remove_one(self, owner, target):
        if owner._id in target._reference_fields[self.id_field]:
            return
        target._reference_fields[self.id_field].remove(owner._id)
        target.get_collection().update(
            {'_id':target._id},
            {
                '$pull': { self.id_field: owner._id }
            }
        )
        
    def cascade(self, owner, model):
        model.get_collection().remove({
            self.id_field: owner._id
        })


class Local(StoragePolicy):
    """Reference a model(s) using a local field"""
    
    def __init__(self, id_field):
        self.id_field = id_field
        
        
    def get_owner_reference_field(self, owner):
        return self.id_field, None
        
        
    def get_one(self, owner, model):
        if owner._reference_fields[self.id_field] is None:
            return None
            
        doc = model.get_collection().find_one(owner._reference_fields[self.id_field])
        
        if not doc:
            return None
        
        return model(**doc)
        
        
    def set_one(self, owner, target):
        owner.get_collection().update(
            {'_id':owner._id},
            {
                '$set': { self.id_field: target._id }
            }
        )
        owner._reference_fields[self.id_field] = target._id
        
        
    def remove_one(self, owner, target):
        owner.get_collection().update(
            {'_id':owner._id},
            {
                '$unset': { self.id_field: True }
            }
        )
        owner._reference_fields[self.id_field] = None
        
        
    def get_many(self, owner, model, spec=None):
        if self.id_field not in owner._reference_fields:
            return CursorProxy(model, None)
        if spec is None:
            spec = {}
        spec['_id'] = {'$in':owner._reference_fields[self.id_field]}
        return CursorProxy(model, model.get_collection().find(spec))
        
        
    def add_to_many(self, owner, target):
        self.set_one(owner, target)
        
        
    def remove_from_many(self, owner, target):
        self.remove_one(owner, target)
        
        
    def cascade(self, owner, model):
        model.get_collection().remove({
            '_id': owner._reference_fields[self.id_field]
        })
        
        
class LocalList(Local):
    
    def get_owner_reference_field(self, owner):
        return self.id_field, []
        
        
    def add_to_many(self, owner, target):
        if target._id in owner._reference_fields[self.id_field]:
            return
            
        owner.get_collection().update(
            {'_id':owner._id},
            {
                '$addToSet': { self.id_field: target._id }
            }
        )
        owner._reference_fields[self.id_field].append(target._id)
        
        
    def remove_one(self, owner, target):
        if target._id not in owner._reference_fields[self.id_field]:
            return
            
        owner._reference_fields[self.id_field].remove(target._id)
        owner.get_collection().update(
            {'_id':owner._id},
            {
                '$pull': { self.id_field: target._id }
            }
        )
        
    def cascade(self, owner, model):
        model.get_collection().remove({
            '_id': { '$in': owner._reference_fields[self.id_field] }
        })


class Join(StoragePolicy):
    """
    Reference models using a join collection
    """
    
    def __init__(self, collection_name, owner_id_field, target_id_field):
        self.collection_name = collection_name
        self.collection = None
        self.owner_id_field = owner_id_field
        self.target_id_field = target_id_field
        
        
    def get_collection(self):
        if not self.collection:
            self.collection = connection.database[self.collection_name]
        return self.collection
        
        
    def get_one(self, owner, model):
        join_doc = self.get_collection().find_one(
            {
                self.owner_id_field: owner._id
            })
        
        if not join_doc:
            return None
        
        doc = model.get_collection().find_one(join_doc['_id'])
        
        if not doc:
            return None
        
        return model(**doc)
        
        
    def set_one(self, owner, target):
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
        
        
    def remove_one(self, owner, target):
        self.get_collection().remove(
            {
                self.owner_id_field: owner._id,
                self.target_id_field: target._id
            }
        )
        
        
    def get_many(self, owner, model, spec=None):
        join_docs = self.get_collection().find(
                                    { self.owner_id_field: owner._id })
        
        if join_docs.count() == 0:
            return CursorProxy(model, join_docs)
        
        target_ids = [doc['_id'] for doc in join_docs]
        return CursorProxy(model, { '_id': {'$in': target_ids} })
        
        
    def add_to_many(self, owner, target):
        self.get_collection().update(
            {
                self.owner_id_field: owner._id,
                self.target_id_field: target._id
            },
            upsert=True
        )
        
        
    def remove_from_many(self, owner, target):
        self.remove_one(owner, target)
        
        
    def cascade(self, owner, model):
        pass
