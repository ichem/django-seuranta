class B64Codec(object):
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
