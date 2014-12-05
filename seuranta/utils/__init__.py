def make_random_code(length):
    import random
    random.seed()
    alpha = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    out = ''
    for i in range(length):
        out += alpha[random.randrange(len(alpha))]
    return out


def format_date_iso(val):
    from django.utils.timezone import utc
    return (val.astimezone(utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(s):
    from django.template.defaultfilters import slugify as _slugify
    try:
        from unidecode import unidecode
        s = unidecode(s)
    except:
        pass
    return _slugify(s)


def format_size(amount, si=True):
    unit = "B"
    thresh = 1e3 if si else 1 << 10
    if not si:
        unit = u"i%s" % unit
    unit_prefix = [
        u'y', u'z', u'a', u'f', u'p', u'n',
        u'\u00b5',   # Mu
        u'm', u'', u'k', u'M',
        u'G', u'T', u'P', u'E', u'Z', u'Y'
    ]
    ui = 8
    sign = ''
    amount = float(amount)
    if amount < 0:
        sign = u'-'
        amount = -amount
    while True:
        if (1 <= amount < thresh) \
           or ui == len(unit_prefix)-1 \
           or ui == 0 \
           or amount == 0:
            break
        if amount <= 1:
            amount *= thresh
            ui -= 1
        else:
            amount /= thresh
            ui += 1
    return u"%s%.1f%s%s" % (sign, amount, unit_prefix[ui], unit)


def short_uuid():
    import uuid
    return uuid.uuid4().bytes.encode('base64').rstrip('=\n')\
        .replace('/', '_').replace('+', '-')


def short_sha256(val):
    from hashlib import sha256
    return sha256(val).digest().encode('base64')\
        .rstrip('=\n').replace('/', '_').replace('+', '-')


def cmp_float(a, b):
    if abs(a-b) < 1e-9:
        return 0
    elif a-b < 0:
        return -1
    else:
        return 1


def solve_affine_matrix(r1, s1, t1, r2, s2, t2, r3, s3, t3):
    a = (((t2 - t3) * (s1 - s2)) - ((t1 - t2) * (s2 - s3))) \
        / (((r2 - r3) * (s1 - s2)) - ((r1 - r2) * (s2 - s3)))
    b = (((t2 - t3) * (r1 - r2)) - ((t1 - t2) * (r2 - r3))) \
        / (((s2 - s3) * (r1 - r2)) - ((s1 - s2) * (r2 - r3)))
    c = t1 - (r1 * a) - (s1 * b)
    return a, b, c


def derive_affine_transform(a0x, a0y, a1x, a1y, b0x, b0y, b1x, b1y, c0x, c0y,
                            c1x, c1y):
    x = solve_affine_matrix(
        a0x, a0y, a1x,
        b0x, b0y, b1x,
        c0x, c0y, c1x
    )
    y = solve_affine_matrix(
        a0x, a0y, a1y,
        b0x, b0y, b1y,
        c0x, c0y, c1y
    )
    return tuple(x+y)


def remote_file_exist(url):
    import requests
    try:
        requests.head(url).raise_for_status()
        return True
    except:
        return False
