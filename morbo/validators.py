"""
This package provides a simple validation system as well as a number of 
validators and converters. You'll probably find it's usage familiar.

Validators generally perform one task: check that a value meets a certain
specification. Sometimes they also perform a conversion. For instance, a time
validator might validate that a value is in one of a number of formats and then
convert the value to, say, a datetime instance or a POSIX timestamp.

This package contains quite a few useful validators but doesn't even try to include 
the kitchen sink. Most applications will have their own validation requirements and 
the thinking here is to make it as easy as possible to create new validators, rather
than create a library that covers all cases.

So, creating validators is straightforward. Subclass Validator and implement 
the validate() method. That's all that's required. Here is an example that will 
only validate yummy things. Optionally, it will convert to yumminess level::

    class Yummy(Validator):
        yumminess = {
            'Pizza': 1.5,
            'Pie': 2.75,
            'Steak': 5.58,
            'Sushi': 14.62,
            'Duck Confit': 28.06
        }
        
        def __init__(self, should_convert=False, *args, **kwargs):
            self.should_convert = should_convert
            super(Yummy, self).__init__(*args, **kwargs)
            
            
        def validate(self, value):
            if value not in self.yumminess:
                raise InvalidError('Yumminess not known for "%s"' % value)
            
            if self.should_convert:
                return self.yumminess[value]
            
            return value

It's a convention, but not a requirement, to put error values in the class like so::

    class Yummy(Validator):
        NOT_YUMMY = "This is not yummy"
        
        def validate(self, value):
            if not self.is_yummy(value):
                raise InvalidError(self.NOT_YUMMY)

Then we can do things based on the type of error, if we so desire::

    yummy_validator = Yummy()
    try:
        yummy_validator.validate('Fried Okra')
        print "Fried Okra is yummy!"
    except InvalidError, e:
        if e.message == Yummy.NOT_YUMMY:
            print "Fried Okra is not yummy"
        else:
            print "There is something wront with Fried Okra"

"""

import re


class InvalidError(Exception):
    """
    This exception is thrown by all validators to indicate that data is invalid.
    If you subclass Validator, throw this in validate().
    """


class InvalidGroupError(Exception):
    """
    This exception represents a group of invalid errors. It takes a dict where
    the keys are, presumably, the names of items that were invalid and the values
    are the errors for their respective items.
    """
    
    def __init__(self, errors):
        self.errors = errors
        super(CompoundInvalid, self).__init__(
            "Some errors were encountered\n" + \
            '\n'.join(["%s: %s" % (k,v) for k,v in errors.items()]))



class Validator(object):
    """
    This is the base validator class. Don't use it unless you are inheriting.
    """
    
    def __init__(self, optional=False):
        self.optional = optional
    
    def validate(self, value):
        raise NotImplementedError
        
    def default_value(self):
        raise NotImplementedError


class Text(Validator):
    """
    Validate that a value is text and, optionally, that it meets a length specification.
    """
    NOT_TEXT = 'Expected some text.'
    TOO_SHORT = 'This text is too short.'
    TOO_LONG = 'This text is too long.'
    
    def __init__(self, minlength=None, maxlength=None, *args, **kwargs):
        self.minlength = minlength
        self.maxlength = maxlength
        super(Text, self).__init__(*args, **kwargs)
        
    def validate(self, value):
        if not isinstance(value, basestring):
            raise InvalidError(self.NOT_TEXT)
            
        if self.minlength is not None and len(value) < self.minlength:
            raise InvalidError(self.TOO_SHORT)
            
        if self.maxlength is not None and len(value) > self.maxlength:
            raise InvalidError(self.TOO_LONG)
            
        return value


class Email(Validator):
    """Validates strings that meet the guidelines in `RFC 3696 <http://tools.ietf.org/html/rfc3696>`_"""
    pattern = re.compile("((\"[^@]+\")|((\\[^@]))|([\d\w\!#\$%&'\*\+\-/=\?\^_`\{\|\}~]))((\"[^@]+\")|(\\[^@])|([\d\w\!#\$%&'\*\+\-/=\?\^_`\.\{\|\}~]))*@[a-zA-Z0-9]+([a-zA-Z0-9\-][a-zA-Z0-9]+)?(\.[a-zA-Z0-9]+([a-zA-Z0-9\-][a-zA-Z0-9]+)?)+\.?$")
    
    def validate(self, value):
        if not self.pattern.match(value):
            raise InvalidError("Invalid email address.")


class DateTime(Validator):
    """Validates many representations of date & time and converts to datetime.datetime.
    It will use `timelib <http://pypi.python.org/pypi/timelib/>`_ if available,
    next it will try `dateutil.parser <http://labix.org/python-dateutil>`_. If neither
    is found, it will use :func:`datetime.strptime` with some predefined format string.
    """
    
    try:
        import timelib
        strtodatetime = timelib.strtodatetime
    except ImportError:
        try:
            from dateutil import parser as date_parser
            strtodatetime = date_parser.parse
        except ImportError:
            strtodatetime = None
    
    def __init__(self, now=False, default_format="", *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)
        self.default_format = default_format
        self.now = now


class PhoneNumber(Validator):
    pass
