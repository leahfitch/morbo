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
        registry.clear()
    
    
    def test_one(self):
        class Foo(Model):
            bar = One("Bar")
            
        class Bar(Model):
            pass
            
        foo = Foo()
        bar = Bar()
        with self.assertRaises(AssertionError):
            foo.bar = bar
        bar.save()
        foo.bar = bar
        self.assertEquals(foo.bar, bar)
        foo.save()
        foo = Foo.find_one(foo._id)
        self.assertEquals(foo.bar, bar)
        
        
    def test_one_no_inverse(self):
        with self.assertRaises(TypeError):
            class Foo(Model):
                bar = One("Bar", inverse="foo")
                
                
    def test_one_to_one(self):
        class Foo(Model):
            bar = OneToOne("Bar", inverse="foo")
            
        class Bar(Model):
            pass
        
        bar = Bar()
        bar.save()
        foo = Foo()
        foo.save()
        foo.bar = bar
        foo.save()
        self.assertEquals(bar.foo, foo)
        
        
    def test_one_to_one_overdefined(self):
        class Foo(Model):
            bar = OneToOne("Bar", inverse="foo")
        
        class Bar(Model):
            foo = OneToOne(Foo, inverse="bar")
            
        bar = Bar()
        bar.save()
        foo = Foo()
        foo.save()
        foo.bar = bar
        foo.save()
        self.assertEquals(bar.foo, foo)

if __name__ == "__main__":
    unittest.main()
