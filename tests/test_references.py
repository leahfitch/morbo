"""
Unit tests for references
"""
import unittest
from morbo import *


#class User(Model):
#    friends = Many('User', Join('user_id', 'friend_id'))
#    posts = Many('Post', Remote('author_id'))
#    hats = Many('Hat', LocalList('hat_ids'))
#    weapon_of_choice = One('weapon', Local('weapon_id'))
#    comments = Many('Comment', Embedded())
#    steed = One('Horse', Embedded())


class ReferencesTestCase(unittest.TestCase):
    
    def setUp(self):
        for c in connection.database.collection_names():
            try:
                connection.database.drop_collection(c)
            except:
                pass


if __name__ == "__main__":
    unittest.main()
