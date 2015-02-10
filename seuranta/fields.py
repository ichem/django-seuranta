import uuid
try:
    from django.utils.encoding import force_unicode  # NOQA
except ImportError:
    from django.utils.encoding import force_text as force_unicode  # NOQA
from django.utils.translation import ugettext_lazy as _
from django.db.models import Field, SubfieldBase
from django.core.exceptions import ValidationError
from seuranta.utils.b64_codec import UrlSafeB64Codec


class ShortUUIDField(Field):
    __metaclass__ = SubfieldBase
    """
    ShortUUIDDField
    Automatic CharField that provide a Base64 encoded UUID4.
    """
    def __init__(self, *args, **kwargs):
        if hasattr(kwargs, 'max_length'):
            raise ValueError("Illegal parameter 'max_length'")
        if hasattr(kwargs, 'editable'):
            raise ValueError("Illegal parameter 'editable'")
        self.empty_strings_allowed = False
        kwargs['blank'] = True
        kwargs['editable'] = False
        kwargs['max_length'] = 22
        super(ShortUUIDField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ShortUUIDField, self).deconstruct()
        del kwargs['blank']
        del kwargs['editable']
        del kwargs['max_length']
        return name, path, args, kwargs

    def get_internal_type(self):
        return 'CharField'

    def validate(self, value, model_instance):
        try:
            hex_val = str(uuid.UUID(bytes=UrlSafeB64Codec.decode(value)))
        except ValueError:
            raise ValidationError(_(u'This is not a valid UUID'))
        if int(hex_val[14], 16) != self.version \
                or int(hex_val[19], 16) & 0xc != 8:
            raise ValidationError(_(u'This is not a valid UUID4'))
        super(ShortUUIDField, self).validate(value, model_instance)

    def pre_save(self, model_instance, add):
        value = super(ShortUUIDField, self).pre_save(model_instance, add)
        if add and (value is None or not value):
            value = force_unicode(UrlSafeB64Codec.encode(uuid.uuid4().bytes))
            setattr(model_instance, self.attname, value)
        return value
