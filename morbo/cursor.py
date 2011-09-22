class CursorProxy(object):
    
    def __init__(self, model, cursor):
        self._model = model
        self._cursor = cursor
        
        
    def __getitem__(self, index):
        return self._model(self._cursor.__getitem__(index))
        
        
    def __getattr__(self, name):
        return getattr(self._cursor, name)
        
        
    def next(self):
        return self._model(**self._cursor.next())
        
