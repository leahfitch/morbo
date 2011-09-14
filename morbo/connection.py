from pymongo import Connection

database = None

def setup(db="test", **kwargs):
    global database
    connection = Connection(**kwargs)
    database = connection[db]
