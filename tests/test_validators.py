#!/usr/bin/python
"""
Unit tests for data validators
"""
import unittest
from morbo.validators import *
from datetime import datetime
import time


class ValidatorsTestCase(unittest.TestCase):
    
    def test_validator_abstract(self):
        """
        Shouldn't be able to use base Validator as a validator
        """
        v = Validator()
        self.assertRaises(NotImplementedError, v.validate, 23)
        
        
class TextTestCase(unittest.TestCase):
        
    def test_not_text(self):
        """
        Should raise InvalidError for anything but a string
        """
        v = Text()
        self.assertRaises(InvalidError, v.validate, 23)
        
        
    def test_text(self):
        """
        Should not raise InvalidError for text
        """
        v = Text()
        try:
            v.validate("foo")
        except InvalidError:
            self.fail("Text.validate() raised InvalidError for a string")
            
            
    def test_minlength_success(self):
        """
        Should not raise InvalidError if a string is longer than minlength.
        """
        test_string = "foofoo"
        v = Text(minlength=len(test_string)-1)
        
        try:
            v.validate(test_string)
        except InvalidError:
            self.fail("Text.validate(minlength=%d) raised InvalidError for a string of length %d" %(
                len(test_string)-1, len(test_string)))
            
            
    def test_minlength_fail(self):
        """
        Should raise InvalidError if a string is shorter than minlength.
        """
        test_string = "foofoo"
        v = Text(minlength=len(test_string)+1)
        self.assertRaises(InvalidError, v.validate, test_string)
        
        
    def test_maxlength_success(self):
        """
        Should not raise InvalidError if a string's length is less than or equal to maxlength
        """
        test_string = "foofoo"
        test_string_len = len(test_string)
        v = Text(maxlength=test_string_len)
        
        try:
            v.validate(test_string)
        except InvalidError:
            self.fail("Text.validate(maxlength=%d) raised InvalidError for a string of length %d" %(
                test_string_len, test_string_len))
            
            
        v = Text(maxlength=test_string_len+1)
        
        try:
            v.validate(test_string)
        except InvalidError:
            self.fail("Text.validate(maxlength=%d) raised InvalidError for a string of length %d" %(
                test_string_len+1, test_string_len))
            
            
    def test_maxlength_fail(self):
        """
        Should raise InvalidError if a string is longer than maxlength
        """
        test_string = "foofoo"
        v = Text(maxlength=len(test_string)-1)
        self.assertRaises(InvalidError, v.validate, test_string)
        
        
    def test_return_value(self):
        """
        Should always return the input value
        """
        string = "foobarbaz"
        v = Text(minlength=1,maxlength=23)
        self.assertEqual(string, v.validate(string))
        
        
class TestEmailCase(unittest.TestCase):
    
    def test_fail(self):
        """
        Should raise InvalidError on things that aren't email addresses
        """
        v = Email()
        not_emails = [
            23,
            "foo",
            "@foo.com"
        ]
        
        for not_email in not_emails:
            self.assertRaises(InvalidError, v.validate, not_email)
        
        
    def test_pass(self):
        """
        Should accept addresses that meet the guidelines in RFC 3696
        """
        emails = [
            'foo@example.com',
            'a@b.c',
            'foo@exa.amp.le.com',
            'foo_bar@example.com.',
            'foo.bar@example.com',
            'f!o#o$b%a&r\'b*a+z-b/a=n?g^b_i`f.b{o|p}~@example.com',
            '"some white space"@example.com',
            '\@fo"   "\//o@example.com'
        ]
        
        v = Email()
        
        for email in emails:
            try:
                self.assertEquals(email, v.validate(email))
            except InvalidError:
                self.fail('Failed to accept %s' % email)
        
        
        
class TestDateTime(unittest.TestCase):
    
    def test_fail(self):
        """
        Should raise invalid for things that aren't dates and times
        """
        v = DateTime()
        not_datetimes = [
            "santa claus",
            "the cure is wednesday",
            "324"
        ]
        
        for not_datetime in not_datetimes:
            self.assertRaises(InvalidError, v.validate, not_datetime)
        
        
    def test_simple(self):
        """
        Should parse dates in the default format and return them as datetime objects.
        """
        v = DateTime(default_format="%D")
        bday = datetime(1982, 9, 6)
        
        try:
            self.assertEqual(bday, v.validate('9/6/82'))
        except InvalidError:
            self.fail('Failed to validate 9/6/82 with format %D')
        
        
    def test_timelib(self):
        """
        If timelib is installed, should be able to parse stuff like "today"
        """
        try:
            import timelib
        except ImportError:
            print "timelib is not installed, skipping timelib test for DateTime validator"
            return
        
        v = DateTime(use_timelib=True, use_dateutil=False)
        today = datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
        
        try:
            self.assertEqual(today, v.validate("today"))
        except InvalidError:
            self.fail('timelib enabled validator didn\'t pass "today"')
        
        
    def test_dateutil(self):
        """
        If dateutil is installed, should be able to parse formats other than the default
        """
        try:
            import dateutil
        except ImportError:
            print "dateutil is not installed, skipping dateutil test for DateTime validator"
            return
        
        v = DateTime(default_format="%d", use_timelib=False, use_dateutil=True)
        bday = datetime(1982,9,6)
        
        try:
            self.assertEqual(bday, v.validate('9/6/82'))
        except InvalidError:
            self.fail('dateutil enabled validator didn\'t pass "9/6/82"')
            
            
    def test_reflexive(self):
        """
        Should pass and return a datetime.datetime instance.
        """
        v = DateTime()
        now = datetime.now()
        
        try:
            self.assertEquals(now, v.validate(now))
        except InvalidError:
            self.fail("Failed to pass a datetime.datetime instance")
            
            
    def test_timestamp(self):
        """
        Should pass both int and float timestamps and convert to utc datetime
        """
        v = DateTime()
        now = time.time()
        now_date = datetime.utcfromtimestamp(now)
        
        try:
            self.assertEquals(now_date, v.validate(now))
        except InvalidError:
            self.fail("Failed to pass a float timestamp")
            
        now = int(now)
        now_date = datetime.utcfromtimestamp(now)
        
        try:
            self.assertEquals(now_date, v.validate(now))
        except InvalidError:
            self.fail("Failed to pass an int timestamp")
        
        
class TestBool(unittest.TestCase):
    
    def test_fail(self):
        """
        Should raise InvalidError for things that don't represent booleans
        """
        not_bools = [
            "maybe",
            67,
            dict
        ]
        
        v = Bool()
        
        for not_bool in not_bools:
            self.assertRaises(InvalidError, v.validate, not_bool)
        
        
    def test_falses(self):
        """
        Should pass and convert several represenations of False
        """
        falses = [
            False,
            0,
            "0",
            "false",
            "FALSE",
            "fAlSe",
            "no",
            "No"
        ]
        
        v = Bool()
        
        for false in falses:
            try:
                self.assertEqual(False, v.validate(false))
            except InvalidError:
                self.fail("Didn't pass '%s'" % false)
        
        
    def test_falses(self):
        """
        Should pass and convert several represenations of True
        """
        trues = [
            True,
            1,
            "1",
            "true",
            "TRUE",
            "TruE",
            "yes",
            "yEs"
        ]
        
        v = Bool()
        
        for true in trues:
            try:
                self.assertEqual(True, v.validate(true))
            except InvalidError:
                self.fail("Didn't pass '%s'" % true)
        
        
        
class TestBoundingBox(unittest.TestCase):
    
    def test_fail(self):
        """
        Shouldn't pass things that aren't a bounding box.
        """
        not_bboxes = [
            "fred",
            (1,3,4),
            ["apples", 42, 24, 6],
            (1,181,3,-300),
            348.345
        ]
        v = BoundingBox()
        
        for not_bbox in not_bboxes:
            try:
                v.validate(not_bbox)
                self.fail("Passed '%s'" % (not_bbox,))
            except InvalidError:
                pass
        
        
    def test_list(self):
        """
        Should pass a list or tuple
        """
        box = [42.75804,-85.0031, 42.76409, -84.9861]
        v = BoundingBox()
        
        try:
            v.validate(box)
        except InvalidError:
            self.fail("Failed '%s'", box)
            
        box = tuple(box)
        
        try:
            v.validate(box)
        except InvalidError:
            self.fail("Failed '%s'", box)
        
        
    def test_string(self):
        """
        Should pass a comma-separated string and convert to a tuple
        """
        box = (42.75804,-85.0031, 42.76409, -84.9861)
        str_box = ",".join([str(b) for b in box])
        v = BoundingBox()
        
        try:
            self.assertEqual(box, v.validate(str_box))
        except InvalidError:
            self.fail("Failed '%s'", str_box)
        
        
class TestLatLng(unittest.TestCase):
    
    def test_fail(self):
        """
        Should throw InvalidError for things that aren't a geographic point
        """
        not_latlngs = [
            14,
            "the whole earf",
            {'foo': 'bar'},
            (181,-181)
        ]
        
        v = LatLng()
        
        for not_latlng in not_latlngs:
            try:
                v.validate(not_latlng)
                self.fail("Passed %s" % (not_latlng,))
            except InvalidError:
                pass
            
            
    def test_pass(self):
        """
        Should pass a list, tuple or comma-separated string.
        """
        latlngs = [
            "42.76066, -84.9929",
            (42.76066, -84.9929),
            [42.76066, -84.9929]
        ]
        
        v = LatLng()
        
        for latlng in latlngs:
            try:
                v.validate(latlng)
            except InvalidError:
                self.fail("Failed to pass %s" % latlng)
        
        
    def test_return_value(self):
        """
        Should always return a 2-tuple of floats
        """
        latlng = (42.76066, -84.9929)
        latlngs = [list(latlng), "%s,%s" % latlng]
        
        v = LatLng()
        
        for l in latlngs:
            self.assertEqual(latlng, v.validate(l))
        
        
class TestEnum(unittest.TestCase):
    
    def test_fail(self):
        """
        Shouldn't pass anything not in the defined list
        """
        values = [5, "atilla the hun", unicode]
        wrong = [8, "ivan the terrible", str]
        
        v = Enum(values)
        
        for w in wrong:
            self.assertRaises(InvalidError, v.validate, w)
            
            
    def test_pass(self):
        """
        Should pass anything in the defined list
        """
        values = [5, "atilla the hun", unicode]
        
        v = Enum(values)
        
        for value in values:
            try:
                self.assertEqual(value, v.validate(value))
            except InvalidError:
                self.fail("Didn't pass %s" % value)
        
        
class TestTypeOf(unittest.TestCase):
    
    def test_fail(self):
        """
        Shouldn't pass values of a type not specified
        """
        v = TypeOf(int)
        self.assertRaises(InvalidError, v.validate, "Hi, hungry?")
        
        
    def test_pass(self):
        """
        Should pass values of the specified type
        """
        v = TypeOf(basestring)
        value = u"foo"
        
        try:
            self.assertEqual(value, v.validate(value))
        except InvalidError:
            self.fail("Didn't pass value of specified type")
        
        
class TestURL(unittest.TestCase):
    
    def test_fail(self):
        """
        Don't pass things that aren't URLs or that don't have the specified schemes.
        """
        not_urls = ["snipe", u'\xe2\x99\xa5', 777, 'huup://foo.bar']
        v = URL(schemes=('http',))
        
        for not_url in not_urls:
            self.assertRaises(InvalidError, v.validate, not_url)
        
        
    def test_pass(self):
        """
        Should pass URLs with the specified schemes.
        """
        urls = [
            'http://example.com',
            'foo://example.com./',
            'http://example.com/foo/bar?baz=goo&snoo=snazz#help',
            'http://127.0.0.1',
            'bar://127.0.0.1:80'
        ]
        v = URL(schemes=('http', 'foo', 'bar'))
        
        for url in urls:
            try:
                self.assertEqual(url, v.validate(url))
            except InvalidError:
                self.fail("Didn't pass '%s'" % url)
        
        
class TestOneOf(unittest.TestCase):
    
    def test_fail(self):
        """
        Should not pass things that don't pass at least one validator.
        """
        bads = [
            "snooze button",
            50
        ]
        v = OneOf((Email(), TypeOf(float)))
        
        for bad in bads:
            self.assertRaises(InvalidError, v.validate, bad)
            
            
    def test_pass(self):
        """
        Should pass anything that matches any of the validators
        """
        goods = [23, 3.1459, "batman", 16]
        v = OneOf((TypeOf(int), Enum((3.1459, "pie", "batman"))))
        
        for good in goods:
            try:
                self.assertEqual(good, v.validate(good))
            except InvalidError:
                self.fail("Failed to pass '%s'" % good)
        
        
class TestListOf(unittest.TestCase):
    
    def test_fail(self):
        """
        Shouldn't pass a list of things that don't pass the validator or things
        that aren't lists.
        """
        bads = [23, [23,24,25]]
        v = ListOf(TypeOf(basestring))
        
        for bad in bads:
            self.assertRaises(InvalidError, v.validate, bad)
            
            
    def test_pass(self):
        """
        Should pass a list of things that pass the validator
        """
        goods = [
            ['a', 15, 'pointy hat'],
            [5],
            ['pancakes', 'alpha centauri', 9]
        ]
        
        v = ListOf(OneOf((TypeOf(basestring), TypeOf(int))))
        
        for good in goods:
            try:
                self.assertEqual(good, v.validate(good))
            except InvalidError:
                self.fail("Failed to pass '%s'", good)
        
        
if __name__ == "__main__":
    unittest.main()
