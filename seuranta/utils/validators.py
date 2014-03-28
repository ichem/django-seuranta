from django.core.exceptions import ValidationError

import uuid

def validate_short_uuid(value):
    if len(value)!=22:
        raise ValidationError(u'This is not a valid uuid4')
    value_b64 = "%s=="%value.replace('-', '+').replace('_', '/')
    try:
        val = str(uuid.UUID((value_b64.decode('base64')).encode('hex')))
    except:
        raise ValidationError(u'This is not a valid uuid4')
    if val[14]!="4" or val[19] not in "89ab":
        raise ValidationError(u'This is not a valid uuid4')
