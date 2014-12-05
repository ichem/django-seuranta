import re

VALID_URL_SAFE_B64_CHARS_RE = re.compile('[0-9A-Za-z_-]')
INVALID_URL_SAFE_B64_CHARS_RE = re.compile('[^0-9A-Za-z_-]')
VALID_B58_CHARS_RE = re.compile('[1-9A-HJ-MP-Za-km-z]')
INVALID_B58_CHARS_RE = re.compile('[^0-9A-Za-z_-]|[0IOl_-]')
VALID_B57_CHARS_RE = re.compile('[1-9A-HJ-MP-Za-km-z]')
INVALID_B57_CHARS_RE = re.compile('[^0-9A-Za-z_-]|[0IOl_-]')
BITCOIN_B58_CHARS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZ' \
                    'abcdefghijkmnopqrstuvwxyz'
FLICKR_B58_CHARS = '123456789abcdefghijkmnopqrstuvwxyz' \
                   'ABCDEFGHJKLMNPQRSTUVWXYZ'
RIPPLE_B58_CHARS = 'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ' \
                   '2bcdeCg65jkm8oFqi1tuvAxyz'
WEB_B57_CHARS = INVALID_B57_CHARS_RE.sub('', BITCOIN_B58_CHARS)


# Python 3.x
def _ord(c):
    if str != bytes:
        return c
    return ord(c)


def _chr(i):
    if str != bytes:
        return bytes((i,))
    return chr(i)


class BaseCodec(object):
    def decode(self, v):
        pass

    def encode(self, v):
        pass

    def to_hex(self, val):
        return self.decode(val).encode('hex')

    def from_hex(self, val):
        try:
            return self.encode(val.decode('hex'))
        except (TypeError, ValueError):
            raise ValueError('%s is not an hexadecimal value' % val)


class CustomAlphabetBaseCodec(BaseCodec):
    def __init__(self, alphabet):
        if not isinstance(alphabet, basestring):
            raise TypeError('Alphabet should be a string')
        self.__chars = alphabet
        self.__base = len(alphabet)

    def encode(self, v):
        """
        encode value, which is a string of bytes, to the custom base.
        """
        long_value = 0
        if v == '\0':
            return self.__chars[0]
        for (i, c) in enumerate(v[::-1]):
            long_value += ((1 << (8*i)) * _ord(c))
        result = u''
        while long_value >= self.__base:
            div, mod = divmod(long_value, self.__base)
            result += self.__chars[mod]
            long_value = div
        result += self.__chars[long_value]
        n_pad = 0
        for c in v:
            if c == '\0':
                n_pad += 1
            else:
                break
            result += self.__chars[0]*n_pad
        return result[::-1]

    def decode(self, v):
        """
        decode v into a string of len bytes
        """
        if v == self.__chars[0]:
            return '\0'
        long_value = 0
        for (i, c) in enumerate(v[::-1]):
            long_value += self.__chars.find(c) * (self.__base**i)
        result = bytes()
        while long_value >= 256:
            div, mod = divmod(long_value, 256)
            result += _chr(mod)
            long_value = div
        result += _chr(long_value)
        n_pad = 0
        while n_pad < len(v) and v[n_pad] == self.__chars[0]:
            n_pad += 1
        result += (_chr(0)*n_pad)
        return result[::-1]


BitcoinB58Codec = CustomAlphabetBaseCodec(alphabet=BITCOIN_B58_CHARS)
FlickrB58Codec = CustomAlphabetBaseCodec(alphabet=FLICKR_B58_CHARS)
RippleB58Codec = CustomAlphabetBaseCodec(alphabet=RIPPLE_B58_CHARS)
WebB57Codec = CustomAlphabetBaseCodec(alphabet=WEB_B57_CHARS)


class B64Codec(BaseCodec):
    def __init__(self, char_map=None):
        if char_map is None:
            char_map = {}
        if not isinstance(char_map, dict):
            raise TypeError
        self.char_map = char_map

    def encode(self, v):
        result = v.encode('base64').rstrip('=\n')
        for char, replacement in self.char_map.iteritems():
            result = result.replace(char, replacement)
        return result

    def decode(self, v):
        val_b64 = v
        for char, replacement in self.char_map.iteritems():
            val_b64 = val_b64.replace(replacement, char)
        val_b64 += '=' * (-len(val_b64) % 4)
        result = val_b64.decode('base64')
        return result


UrlSafeB64Codec = B64Codec(char_map={'+': '-', '/': '_'})
