from django.core.exceptions import ValidationError

def validate_latitude(value):
	if value < -90 or value >90:
		raise ValidationError(u'latitude out of range -90.0 90.0')

def validate_longitude(value):
	if value < -180 or value > 180:
		raise ValidationError(u'longitude out of range -180.0 180.0')
