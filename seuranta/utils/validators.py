import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_latitude(value):
    if isinstance(value, (float, int)):
        value = str(value)
    value = Decimal(value)
    if value < -90 or value > 90:
        raise ValidationError(u'latitude out of range -90.0 90.0')


def validate_longitude(value):
    if isinstance(value, (float, int)):
        value = str(value)
    value = Decimal(value)
    if value < -180 or value > 180:
        raise ValidationError(u'longitude out of range -180.0 180.0')


def validate_nice_slug(slug):
    if re.search('[^-a-zA-Z0-9_]', slug):
        raise ValidationError(_(u'Only alphanumeric characters, '
                                u'hyphens and underscores are allowed.'))
    if len(slug) < 5:
        raise ValidationError(_(u'Too short. (min. 5 characters)'))
    elif len(slug) > 21:
        # if 22 characters can be confused with a 'short_uuid'
        raise ValidationError(_(u'Too long. (max. 21 characters)'))
    if slug[0] in "_-":
        raise ValidationError(_(u'Must start with an alphanumeric character.'))
    if slug[-1] in "_-":
        raise ValidationError(_(u'Must end with an alphanumeric character.'))
    if '--' in slug or '__' in slug or '-_' in slug or '_-' in slug:
        raise ValidationError(_(u'Cannot include 2 non alphanumeric '
                                u'character in a row.'))
