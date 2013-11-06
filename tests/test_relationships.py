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
        
        
    def test_one_to_one_cascade(self):
        pass
        
        
    def test_one_to_many(self):
        data = {
            'San Francisco': [
                'Alchemist', 'Bar Tartine', 'Lounge 3411', 'Tempest'
            ],
            'New York': [
                'Dead Rabbit', 'Death & Co.', 'Donna', 'Proletariat'
            ]
        }
        
        class City(Model):
            name = Text()
            bars = OneToMany("Bar", inverse="city")
        
        class Bar(Model):
            name = Text()
        
        for city, bars in data.items():
            c = City(name=city)
            c.save()
            for bar in bars:
                b = Bar(name=bar)
                b.save()
                c.bars.add(b)
        
        city = City.find_one({'name': 'San Francisco'})
        self.assertEquals(city.bars.count(), 4)
        self.assertEquals([b.name for b in city.bars.find().sort('name')], data['San Francisco'])
        
        city = City.find_one({'name': 'New York'})
        self.assertEquals(city.bars.count(), 4)
        self.assertEquals([b.name for b in city.bars.find().sort('name')], data['New York'])
        
        bar = Bar.find_one({'name':'Donna'})
        self.assertEquals(bar.city.name, 'New York')
        self.assertEquals(bar.city, city)
        
        bar.remove()
        self.assertEquals(city.bars.count(), 3)
        
        b = city.bars.find_one()
        name = b.name
        self.assertIn(name, data['New York'])
        city.bars.remove(b)
        self.assertEquals(city.bars.count(), 2)
        new_b = Bar.find_one({'name':name})
        self.assertEquals(b, new_b)
        
        
    def test_one_to_many_over_define(self):
        data = {
            'San Francisco': [
                'Alchemist', 'Bar Tartine', 'Lounge 3411', 'Tempest'
            ],
            'New York': [
                'Dead Rabbit', 'Death & Co.', 'Donna', 'Proletariat'
            ]
        }
        
        class City(Model):
            name = Text()
            bars = OneToMany("Bar", inverse="city")
        
        class Bar(Model):
            name = Text()
            city = ManyToOne(City, inverse="bars")
        
        for city, bars in data.items():
            c = City(name=city)
            c.save()
            for bar in bars:
                b = Bar(name=bar)
                b.save()
                c.bars.add(b)
        
        city = City.find_one({'name': 'San Francisco'})
        self.assertEquals(city.bars.count(), 4)
        self.assertEquals([b.name for b in city.bars.find().sort('name')], data['San Francisco'])
        
        city = City.find_one({'name': 'New York'})
        self.assertEquals(city.bars.count(), 4)
        self.assertEquals([b.name for b in city.bars.find().sort('name')], data['New York'])
        
        bar = Bar.find_one({'name':'Donna'})
        self.assertEquals(bar.city.name, 'New York')
        self.assertEquals(bar.city, city)
        
        bar.remove()
        self.assertEquals(city.bars.count(), 3)
        
        b = city.bars.find_one()
        name = b.name
        self.assertIn(name, data['New York'])
        city.bars.remove(b)
        self.assertEquals(city.bars.count(), 2)
        new_b = Bar.find_one({'name':name})
        self.assertEquals(b, new_b)
        
        
    def test_one_to_many_cascade(self):
        pass
        
        
        
        
if __name__ == "__main__":
    unittest.main()
