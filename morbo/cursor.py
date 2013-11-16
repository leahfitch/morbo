import registry


class CursorProxy(object):
    
    def __init__(self, model, cursor):
        self._model = model
        self._cursor = cursor
        
        
    def _inst(self, fields):
        if '_ib' in fields:
            model_name = fields['_ib'][-1]
            if model_name != self._model.get_full_name():
                return registry.models[model_name](**fields)
        return self._model(**fields)
    
        
    def __getitem__(self, index):
        return self._inst(self._cursor.__getitem__(index))
        
        
    def __getattr__(self, name):
        return getattr(self._cursor, name)
    
    
    def __len__(self):
        return self._cursor.count()
    
        
    def __iter__(self):
        for d in self._cursor:
            yield self._inst(d)
        
    def next(self):
        if self._cursor is None:
            raise StopIteration
        return self._inst(self._cursor.next())
        
    def clone(self):
        return CursorProxy(self, self._model, self._cursor.clone())
        
    def limit(self, n):
        self._cursor.limit(n)
        return self
        
    def skip(self, n):
        self._cursor.skip(n)
        return self
        
    def sort(self, key_or_list, direction=None):
        self._cursor.sort(key_or_list, direction)
        return self
        