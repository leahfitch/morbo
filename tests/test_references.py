"""
Unit tests for references
"""
import unittest
from morbo import *


connection.setup('morbotests')


class TestReferences(unittest.TestCase):
    
    def setUp(self):
        for c in connection.database.collection_names():
            try:
                connection.database.drop_collection(c)
            except:
                pass
            
            
    def test_one_remote_create(self):
        """Should be able to create a remote reference to one model"""
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
        """Should be able to remove a remote reference to one model"""
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
        """Should be able to remove the owner of a remote reference to one model without removing the target"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Remote('a_id'))
            
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(a.b, b)
        
        a.remove()
        
        bb = B.find_one({'skidoo':23})
        self.assertEqual(bb, b)
        
        
    def test_one_remote_remove_owner_cascade(self):
        """Should be able to remove the owner of a remote reference to one model and the target if cascade is True"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Remote('a_id'), cascade=True)
            
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(a.b, b)
        
        a.remove()
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(b, None)
        
        
    def test_one_remote_remove_owner_cascade(self):
        """Should be able to remove all owners of a remote reference to one model and the target if cascade is True"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Remote('a_id'), cascade=True)
            
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(a.b, b)
        
        A.remove()
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(b, None)
        
        
    def test_one_local_create(self):
        """Should be able to create a local reference to one model"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Local('a_id'))
        
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        self.assertEqual(a.b, b)
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        
    def test_one_local_remove(self):
        """Should be able to remove a local reference to one model"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Local('a_id'))
        
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
    
    def test_one_local_remove_owner(self):
        """Should be able to remove the owner of a local reference to one model without removing the target"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Local('a_id'))
            
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(a.b, b)
        
        a.remove()
        
        bb = B.find_one({'skidoo':23})
        self.assertEqual(bb, b)
        
        
    def test_one_local_remove_owner_cascade(self):
        """Should be able to remove the owner of a local reference to one model and the target if cascade is True"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Local('a_id'), cascade=True)
            
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(a.b, b)
        
        a.remove()
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(b, None)
        
        
    def test_one_local_remove_owner_cascade(self):
        """Should be able to remove all owners of a local reference to one model and the target if cascade is True"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Local('a_id'), cascade=True)
            
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(a.b, b)
        
        A.remove()
        
        b = B.find_one({'skidoo':23})
        self.assertEqual(b, None)


if __name__ == "__main__":
    unittest.main()
