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
	sorted_pts = sorted(pts, key=lambda pt: pt['t'])
	p_lat = 0
	p_lon = 0
	p_t = YEAR2000
	encoded_route = ""
	for pt in sorted_pts:
		t = int(pt['t'])
		lat = int(pt['lat']*1e5)
		lon = int(pt['lon']*1e5)

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

class GpsPoint(dict):
	def __hash__(self):
		return hash(self['timestamp'])

def decode(route, since=0):
	r = set([])
	if not route:
		return r

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

		if t >= since:
			r.add(GpsPoint({'t':t, 'lat':lat/1e5, 'lon':lon/1e5}))
	return r
