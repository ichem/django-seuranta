import base64
import random
import struct


def random_key():
    rand_bytes = bytes(struct.pack('Q', random.getrandbits(64)))
    b64 = base64.b64encode(rand_bytes).decode("utf-8")
    b64 = b64[:11]
    b64 = b64.replace('+', '-')
    b64 = b64.replace('/', '_')
    return b64