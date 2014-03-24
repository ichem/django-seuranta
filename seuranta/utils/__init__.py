def slugify(s):
    from django.template.defaultfilters import slugify as _slugify
    try:
        from unidecode import unidecode
        s = unidecode(s)
    except:
        pass
    return _slugify(s)

def formatSize(bytes, si=True):
    thresh = 1000 if si else 1024
    unit = "B" if si else "iB"
    unit_prefix = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    u = 0
    while True:
        if bytes < thresh:
            break
        bytes = bytes*1.0/thresh
        u+=1

    return "%.1f%s%s"%(bytes, unit_prefix[u], unit);

def short_uuid():
    import uuid
    return uuid.uuid4().bytes.encode('base64').rstrip('=\n').replace('/', '_').replace('+', '-')

def cmp_float(a,b):
    if abs(a-b)<1e-9:
        return 0
    elif a-b<0:
        return -1
    else:
        return 1

def solveAffineMatrix(r1, s1, t1, r2, s2, t2, r3, s3, t3):
    a = (((t2 - t3) * (s1 - s2)) - ((t1 - t2) * (s2 - s3))) \
        / (((r2 - r3) * (s1 - s2)) - ((r1 - r2) * (s2 - s3)))
    b = (((t2 - t3) * (r1 - r2)) - ((t1 - t2) * (r2 - r3))) \
        / (((s2 - s3) * (r1 - r2)) - ((s1 - s2) * (r2 - r3)))
    c = t1 - (r1 * a) - (s1 * b)
    return a, b, c

def deriveAffineTransform(a0x, a0y, a1x, a1y, b0x, b0y, b1x, b1y, c0x, c0y, c1x, c1y):
    x = solveAffineMatrix(
        a0x, a0y, a1x,
        b0x, b0y, b1x,
        c0x, c0y, c1x
    )
    y = solveAffineMatrix(
        a0x, a0y, a1y,
        b0x, b0y, b1y,
        c0x, c0y, c1y
    )
    return tuple(x+y)

def remoteFileExist(url):
    import requests
    try:
        requests.head(url).raise_for_status()
        return True
    except:
        return False
