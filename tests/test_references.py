"""
Unit tests for references
"""
import unittest
from morbo import *


connection.setup('morbotests')


class ReferencesTestCase(unittest.TestCase):
    
    def setUp(self):
        for c in connection.database.collection_names():
            try:
                connection.database.drop_collection(c)
            except:
                pass
            
            
    def test_one_remote_create(self):
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Remote('a_id'))
        
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        self.assertEqual(a.b, b)
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        
    def test_one_remote_remove(self):
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Remote('a_id'))
        
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        self.assertEqual(a.b, b)
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        a.b = None
        
        self.assertEqual(a.b, None)
        
        a = A.find_one()
        self.assertEqual(a.b, None)
        
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        del a.b
        
        a = A.find_one()
        self.assertEqual(a.b, None)
    
    def test_one_remote_remove_owner(self):
        pass
    
    def test_one_remote_remove_owner_cascade(self):
        pass


if __name__ == "__main__":
    unittest.main()
