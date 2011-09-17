#!/usr/bin/python
"""
Unit tests for data validators
"""
import unittest
from morbo.validators import *
from datetime import datetime


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
                v.validate(email)
            except InvalidError:
                self.fail('Failed to accept %s' % email)
        
        
    def test_return_value(self):
        """Should always return the input value"""
        
        
        
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
        today = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        
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
        
        
        
if __name__ == "__main__":
    unittest.main()
