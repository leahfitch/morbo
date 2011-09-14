class ValidationError(Exception):
    pass


class CompoundValidationError(Exception):
    
    def __init__(self, errors):
        self.errors = errors
        super(CompoundValidationError, self).__init__(
            "Some errors were encountered\n" + \
            '\n'.join(["%s: %s" % (k,v) for k,v in errors.items()]))


class Validator(object):
    
    def __init__(self, optional=False):
        self.optional = optional
    
    def validate(self, value):
        return value


class Text(Validator):
    
    def __init__(self, length=None, *args, **kwargs):
        self.length = length
        super(Text, self).__init__(*args, **kwargs)
        
    def validator(self, value):
        if not isinstance(value, basestring):
            raise ValidationError('Expected some text.')
            
        if self.length is not None and len(value) > self.length:
            raise ValidationError('This text is too long.')
            
        return value


class Email(Validator):
    pass


class DateTime(Validator):
    
    def __init__(self, now=False, *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)


class PhoneNumber(Validator):
    pass
