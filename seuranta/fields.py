try:
    from django.utils.encoding import force_unicode  # NOQA
except ImportError:
    from django.utils.encoding import force_text as force_unicode  # NOQA
import uuid

from django.utils.translation import ugettext_lazy as _
from django.db.models import Field, SubfieldBase
from django.forms import CharField as CharFieldForm
from django.core.exceptions import ValidationError

from seuranta.utils.custom_base import UrlSafeB64Codec
from seuranta.widgets import Base64UuidWidget


def _b64_uuid_encode(val):
    return UrlSafeB64Codec.encode(val)


def _b64_uuid_decode(val):
    return UrlSafeB64Codec.decode(val)


class ShortUUIDFormField(CharFieldForm):
    def __init__(self, **kwargs):
        self.widget = Base64UuidWidget()
        super(ShortUUIDFormField, self).__init__(**kwargs)


class UuidVersionError(Exception):
    pass


class ShortUUIDField(Field):
    __metaclass__ = SubfieldBase
    """ ShortUUIDDField
    Uses a short version of an UUID version 4 (randomly generated UUID).

    The field support all uuid versions which are natively supported by
    the uuid python module, except version 2.
    For more information see: http://docs.python.org/lib/module-uuid.html
    """
    def validate_version1(self, node, clock_seq):
        if node is None or clock_seq is None:
            raise ValueError("UUID version 1 requires parameters "
                             "node and clock_seq to be set.")
        self.node = node
        self.clock_seq = clock_seq

    def validate_version3_5(self, namespace, name):
        if namespace is None or name is None:
            raise ValueError("UUID version 3 and 5 requires parameters "
                             "namespace and name to be set.")
        self.namespace = namespace
        self.name = name

    def validate_version(self, version, node, clock_seq, namespace, name):
        self.version = version
        if version == 1:
            self.validate_version1(node, clock_seq)
        elif version == 2:
            raise ValueError('UUID version 2 is not supported.')
        elif version == 3 or version == 5:
            self.validate_version3_5(namespace, name)
        elif version != 4:
            raise ValueError("Invalid UUID Version.")

    def flag_illegal_parameters(self, version, node, clock_seq,
                                namespace, name):
        if version != 1:
            if node is not None:
                raise ValueError("Illegal parameter 'node'.")
            if clock_seq is not None:
                raise ValueError("Illegal parameter 'clock_seq'.")
        if version not in (3, 5):
            if name is not None:
                raise ValueError("Illegal parameter 'name'.")
            if namespace is not None:
                raise ValueError("Illegal parameter 'namespace'.")

    def __init__(self, verbose_name=None, name=None, auto=True, version=4,
                 node=None, clock_seq=None, namespace=None,
                 uuid_encode=_b64_uuid_encode, uuid_decode=_b64_uuid_decode,
                 **kwargs):
        if hasattr(kwargs, 'max_length'):
            raise ValueError("Illegal parameter 'max_length'")
        if auto:
            self.empty_strings_allowed = False
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)
        else:
            kwargs.setdefault('editable', True)
        self.auto = auto
        self.flag_illegal_parameters(version, node, clock_seq, namespace, name)
        self.validate_version(version, node, clock_seq, namespace, name)
        tmp_uuid = uuid.uuid4().bytes
        encoded_uuid = uuid_encode(tmp_uuid)
        try:
            assert(tmp_uuid == uuid_decode(encoded_uuid))
        except AssertionError:
            raise ValueError("Invalid encoder/decoder.\n%s\n%s\n%s" % (
                tmp_uuid.encode('hex'),
                uuid_decode(encoded_uuid).encode('hex'),
                encoded_uuid
            ))
        else:
            self.uuid_encode = uuid_encode
            self.uuid_decode = uuid_decode
            kwargs['max_length'] = len(encoded_uuid)
        super(ShortUUIDField, self).__init__(verbose_name, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ShortUUIDField, self).deconstruct()
        del kwargs['max_length']
        if self.auto:
            del kwargs['blank']
        if self.uuid_encode != _b64_uuid_encode:
            kwargs["uuid_encode"] = self.uuid_encode
        if self.uuid_decode != _b64_uuid_decode:
            kwargs["uuid_decode"] = self.uuid_decode
        if self.version != 4:
            kwargs['version'] = self.version
        if self.version == 1:
            kwargs['node'] = self.node
            kwargs['clock_seq'] = self.clock_seq
        if self.version == 3 or self.version == 5:
            kwargs['name'] = self.name
            kwargs['namespace'] = self.namespace
        return name, path, args, kwargs

    def get_internal_type(self):
        return 'CharField'

    def create_uuid(self):
        if self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise UuidVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise UuidVersionError("Invalid UUID version.")

    def create_short_uuid(self):
        attempt = 0
        while True:
            attempt += 1
            short_uuid = self.uuid_encode(self.create_uuid().bytes)
            if len(short_uuid) <= self.max_length:
                return short_uuid
            if attempt >= 1e3:
                raise RuntimeError("Could not generate a UUID matching the ")

    def validate(self, value, model_instance):
        try:
            hex_val = str(uuid.UUID(bytes=self.uuid_decode(value)))
        except ValueError:
            raise ValidationError(_(u'This is not a valid UUID'))
        if self.version in (3, 4, 5) \
           and (int(hex_val[14], 16) != self.version
                or int(hex_val[19], 16) & 0xc != 8):
            raise ValidationError(
                _(u'This is not a valid UUID version %s %s') % (
                    self.version,
                    ", ".join([value, str(len(value)), hex_val, hex_val[14],
                              hex_val[19]])
                )
            )
        super(ShortUUIDField, self).validate(value, model_instance)

    def pre_save(self, model_instance, add):
        value = super(ShortUUIDField, self).pre_save(model_instance, add)
        if self.auto and add and (value is None or not value):
            value = force_unicode(self.create_short_uuid())
            setattr(model_instance, self.attname, value)
        return value

    def formfield(self, **kwargs):
        defaults = {'form_class': ShortUUIDFormField}
        defaults.update(kwargs)
        return super(ShortUUIDField, self).formfield(**defaults)
