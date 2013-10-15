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
            b = One(B, Remote)
        
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
            b = One(B, Remote)
        
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
            b = One(B, Remote)
            
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
            b = One(B, Remote, cascade=True)
            
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
            b = One(B, Remote, cascade=True)
            
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
            b = One(B, Local)
        
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
            b = One(B, Local)
        
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
            b = One(B, Local)
            
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
            b = One(B, Local, cascade=True)
            
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
        
        
    def test_one_join_create(self):
        """Should be able to create a join reference to one model"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Join)
        
        b = B(skidoo=23)
        b.save()
        a = A()
        a.save()
        a.b = b
        
        self.assertEqual(a.b, b)
        
        a = A.find_one()
        self.assertEqual(a.b, b)
        
        
    def test_one_join_remove(self):
        """Should be able to remove a join reference to one model"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Join)
        
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
    
    def test_one_join_remove_owner(self):
        """Should be able to remove the owner of a join reference to one model without removing the target"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Join)
            
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
        
        
    def test_one_join_remove_owner_cascade(self):
        """Should be able to remove the owner of a join reference to one model and the target if cascade is True"""
        class B(Model):
            skidoo = TypeOf(int)
        
        class A(Model):
            b = One(B, Join, cascade=True)
            
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
        
        
    def test_many_remote_create(self):
        """Should be able to create a remote reference to many objects"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Remote)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        bs = list(a.bs.find().sort([('skidoo', 1)]))
        
        self.assertEqual(len(bs), 10)
        self.assertEqual([b.skidoo for b in bs], [23*i for i in range(1,11)])
        
        
    def test_many_remote_remove(self):
        """Should be able to remove a target from a remote many reference"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Remote)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        self.assertEqual(a.bs.find().count(), 10)
        
        b = a.bs.find({'skidoo':69}).next()
        
        self.assertEqual(b.skidoo, 69)
        
        a.bs.remove(b)
        
        self.assertEqual(a.bs.find().count(), 9)
        self.assertEqual(a.bs.find({'skidoo':69}).count(), 0)
        
        
    def test_many_remote_remove_owner(self):
        """Should be able to remove an owner without removing its many remote targets"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Remote)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        self.assertEqual(a.bs.find().count(), 10)
        self.assertEqual(B.find().count(), 10)
        
        a.remove()
        
        self.assertEqual(a.bs.find().count(), 0)
        self.assertEqual(B.find().count(), 10)
        
    def test_many_remote_remove_owner_cascade(self):
        """Should be able to remove an owner and its many remote targets if cascade is true"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Remote, cascade=True)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        self.assertEqual(a.bs.find().count(), 10)
        self.assertEqual(B.find().count(), 10)
        
        a.remove()
        
        self.assertEqual(a.bs.find().count(), 0)
        self.assertEqual(B.find().count(), 0)
        
    def test_many_local_create(self):
        """Should be able to create a local reference to many objects"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Local)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        bs = list(a.bs.find().sort([('skidoo', 1)]))
        
        self.assertEqual(len(bs), 10)
        self.assertEqual([b.skidoo for b in bs], [23*i for i in range(1,11)])
        
        
    def test_many_local_remove(self):
        """Should be able to remove a target from a local many reference"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Local)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        self.assertEqual(a.bs.find().count(), 10)
        
        b = a.bs.find({'skidoo':69}).next()
        
        self.assertEqual(b.skidoo, 69)
        
        a.bs.remove(b)
        
        self.assertEqual(a.bs.find().count(), 9)
        self.assertEqual(a.bs.find({'skidoo':69}).count(), 0)
        
        
    def test_many_local_remove_owner(self):
        """Should be able to remove an owner without removing its many local targets"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Local)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        self.assertEqual(a.bs.find().count(), 10)
        self.assertEqual(B.find().count(), 10)
        
        a.remove()
        
        self.assertEqual(B.find().count(), 10)
        
    def test_many_local_remove_owner_cascade(self):
        """Should be able to remove an owner and its many local targets if cascade is true"""
        class B(Model):
            skidoo = TypeOf(int)
            
        class A(Model):
            bs = Many(B, Local, cascade=True)
            
        a = A()
        a.save()
        
        for i in range(1,11):
            b = B()
            b.skidoo = 23 * i
            b.save()
            a.bs.add(b)
        
        self.assertEqual(a.bs.find().count(), 10)
        self.assertEqual(B.find().count(), 10)
        
        a.remove()
        
        self.assertEqual(B.find().count(), 0)


if __name__ == "__main__":
    unittest.main()
