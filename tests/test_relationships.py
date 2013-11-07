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
        self.assertEquals(bar.foo, foo)
        
        
    def test_one_to_one_cascade(self):
        class Foo(Model):
            bar = OneToOne("Bar", inverse="foo", cascade=True)
        
        class Bar(Model):
            pass
            
        bar = Bar()
        bar.save()
        bar2 = Bar()
        bar2.save()
        foo = Foo()
        foo.save()
        foo.bar = bar
        self.assertEquals(Bar.count(), 2)
        foo.remove()
        self.assertEquals(Bar.count(), 1)
        b = Bar.find_one()
        self.assertEquals(b, bar2)
        
        
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
        class City(Model):
            name = Text()
            bars = OneToMany("Bar", inverse="city", cascade=True)
        
        class Bar(Model):
            name = Text()
        
        city_a = City(name="Foo City")
        city_a.save()
        
        city_b = City(name="Qux City")
        city_b.save()
        
        for i in range(0,10):
            b = Bar(name="Bar a#%s" % str(i+1))
            b.save()
            city_a.bars.add(b)
            
            b = Bar(name="Bar b#%s" % str(i+1))
            b.save()
            city_b.bars.add(b)
        
        self.assertEquals(Bar.count(), 20)
        city_a.remove()
        self.assertEquals(Bar.count(), 10)
        
        b = Bar.find().sort('name').next()
        self.assertEquals(b.name, "Bar b#1")
        
        
    def test_many_to_many(self):
        tags_by_doc = {
            "foo": ["tofu", "seitan"],
            "bar": ["seitan"],
            "baz": ["tempeh", "tofu"],
            "qux": ["seitan", "tofu"],
            "goo": ["seitan"]
        }
        docs_by_tag = {}
        
        class Document(Model):
            content = Text()
            tags = ManyToMany("Tag", inverse="documents")
            
        class Tag(Model):
            name = Text()
        
        tags = {}
        docs = {}
        
        for content, tag_names in tags_by_doc.items():
            doc = Document(content=content)
            doc.save()
            docs[content] = doc
            
            for n in tag_names:
                if n not in tags:
                    tag = Tag(name=n)
                    tag.save()
                    tags[n] = tag
                doc.tags.add(tags[n])
                if n not in docs_by_tag:
                    docs_by_tag[n] = []
                docs_by_tag[n].append(content)
        
        for d in [tags_by_doc, docs_by_tag]:
            for k in d:
                d[k].sort()
        
        for k,v in tags_by_doc.items():
            doc = Document.find_one({'content':k})
            self.assertEquals([tag.name for tag in doc.tags.find().sort('name')], v)
            
        for k,v in docs_by_tag.items():
            tag = Tag.find_one({'name':k})
            self.assertEquals([doc.content for doc in tag.documents.find().sort('content')], v)
        
        tag = Tag.find_one({'name':'seitan'})
        self.assertEquals(tag.documents.count(), 4)
        doc = tag.documents.find_one()
        self.assertIn('seitan', [tag.name for tag in doc.tags])
        num_doc_tags = doc.tags.count()
        tag.documents.remove(doc)
        self.assertEquals(tag.documents.count(), 3)
        self.assertEquals(doc.tags.count(), num_doc_tags-1)
        
        
if __name__ == "__main__":
    unittest.main()
