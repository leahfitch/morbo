#!/usr/bin/python
"""
Unit tests for data validators
"""
import unittest
from morbo.validators import *


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
        
        
if __name__ == "__main__":
    unittest.main()
