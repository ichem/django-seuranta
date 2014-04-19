try:
    from django.utils.encoding import force_unicode  # NOQA
except ImportError:
    from django.utils.encoding import force_text as force_unicode  # NOQA

try:
    import uuid
    HAS_UUID = True
except ImportError:
    HAS_UUID = False

from django.db.models import CharField
from django.core.exceptions import ImproperlyConfigured, ValidationError

class UUIDVersionError(Exception):
    pass

class ShortUUIDField(CharField):
    """ ShortUUIDField

    Uses a short version of an UUID version 4 (randomly generated UUID).

    The field support all uuid versions which are natively supported by the uuid python module, except version 2.
    For more information see: http://docs.python.org/lib/module-uuid.html
    """

    def __init__(self, verbose_name=None, name=None, auto=True, version=4, node=None, clock_seq=None, namespace=None, **kwargs):
        if not HAS_UUID:
            raise ImproperlyConfigured("'uuid' module is required for ShortUUIDField. (Do you have Python 2.5 or higher installed ?)")
        kwargs.setdefault('max_length', 22)
        if auto:
            self.empty_strings_allowed = False
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)
        self.auto = auto
        self.version = version
        if version == 1:
            self.node, self.clock_seq = node, clock_seq
        elif version == 3 or version == 5:
            self.namespace, self.name = namespace, name
        CharField.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return CharField.__name__

    def create_uuid(self):
        if not self.version or self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)

    def create_short_uuid(self):
        return self.create_uuid().bytes.encode('base64').rstrip('=\n').replace('/', '_').replace('+', '-')

    def validate(self, value):
        if len(value)!=22:
            raise ValidationError(u'This is not a valid uuid4')
        value_b64 = "%s=="%value.replace('-', '+').replace('_', '/')
        try:
            val = str(uuid.UUID((value_b64.decode('base64')).encode('hex')))
        except:
            raise ValidationError(u'This is not a valid UUID')

        version_lookup = 4 if not self.version else self.version
        if (not self.version or self.version in [3, 4, 5]) and \
           (val[14]!=version_lookup or val[19] not in "89ab"):
            raise ValidationError(u'This is not a valid UUID version %d'%version_lookup)

    def pre_save(self, model_instance, add):
        value = super(ShortUUIDField, self).pre_save(model_instance, add)
        if self.auto and add and value is None:
            value = force_unicode(self.create_short_uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            if self.auto and not value:
                value = force_unicode(self.create_short_uuid())
                setattr(model_instance, self.attname, value)
        return value

    def formfield(self, **kwargs):
        if self.auto:
            return None
        return super(ShortUUIDField, self).formfield(**kwargs)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
