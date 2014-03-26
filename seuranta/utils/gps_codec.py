from globetrotting import GeoLocation

def encodeNumber(num):
	encoded = "";
	while (num >= 0x20):
		encoded += chr((0x20 | (num & 0x1f)) + 63)
		num = num >> 5

	encoded += chr(num + 63)
	return encoded

def encodeSignedNumber(num):
	sgn_num = num << 1
	if num < 0:
		sgn_num = ~(sgn_num)
	return encodeNumber(sgn_num)

def decodeNumber(encoded):
	enc_len = len(encoded)
	i=0
	shift = 0
	result = 0
	b = 0x20
	while b >= 0x20 and i<enc_len:
		b = ord(encoded[i]) - 63
		i += 1
		result |= (b & 0x1f) << shift
		shift += 5
	if result&1:
		return ~(result>>1), encoded[i:]
	else:
		return result>>1, encoded[i:]

YEAR2000=946684800

def encode(pts):
	sorted_pts = sorted(pts, key=lambda pt: pt.timestamp)
	p_lat = 0
	p_lon = 0
	p_t = YEAR2000
	encoded_route = ""

	for pt in sorted_pts:
		t = int(pt.timestamp)
		lat = int(float(pt.coordinates.latitude)*1e5)
		lon = int(float(pt.coordinates.longitude)*1e5)

		dt = t - p_t
		dlat = lat - p_lat
		dlon = lon - p_lon

		encoded_route += encodeSignedNumber(dt)
		encoded_route += encodeSignedNumber(dlat)
		encoded_route += encodeSignedNumber(dlon)

		p_t = p_t+dt
		p_lat = p_lat+dlat
		p_lon = p_lon+dlon

	return encoded_route

def decode(route, since=None):
	if not route:
		return None

	r = set([])

	lat = 0
	lon = 0
	t = YEAR2000

	while len(route)>0:
		dt, route = decodeNumber(route)
		dlat, route = decodeNumber(route)
		dlon, route = decodeNumber(route)

		lat += dlat
		lon += dlon
		t += dt

		if not since or t >= since:
			r.add(GeoLocation(t, (lat/1e5, lon/1e5)))

	return sorted(r, key=lambda pt: pt.timestamp)
