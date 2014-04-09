from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import uuid
import re

def validate_short_uuid(value):
    if len(value)!=22:
        raise ValidationError(_(u'This is not a valid uuid4'))
    value_b64 = "%s=="%value.replace('-', '+').replace('_', '/')
    try:
        val = str(uuid.UUID((value_b64.decode('base64')).encode('hex')))
    except:
        raise ValidationError(_(u'This is not a valid uuid4'))
    if val[14]!="4" or val[19] not in "89ab":
        raise ValidationError(_(u'This is not a valid uuid4'))

def validate_nice_slug(slug):
    if re.search('[^-a-zA-Z0-9_]', slug):
        raise ValidationError(_(u'Only alphanumeric characters, hyphens and underscores are allowed.'))

    if len(slug) < 5:
        raise ValidationError(_(u'Too short. (min. 5 characters)'))
    elif len(slug) > 21:
        #if 22 characters can be confused with a 'short_uuid'
        raise ValidationError(_(u'Too long. (max. 21 characters)'))

    if slug[0] in "_-":
        raise ValidationError(_(u'Must start with an alphanumeric character.'))

    if slug[-1] in "_-":
        raise ValidationError(_(u'Must end with an alphanumeric character.'))

    if '--' in slug or '__' in slug or '-_' in slug or '_-' in slug:
        raise ValidationError(_(u'Cannot include 2 non alphanumeric character in an row.'))
