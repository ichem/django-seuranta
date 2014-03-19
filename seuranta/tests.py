
# Create your tests here.
import datetime
from django.utils import timezone

utc = timezone.utc
tz = timezone("Europe/Paris")

now = timezone.now()
print now
local = utc.localize(utc.localize(value.replace(tzinfo=None)).astimezone(tz).replace(tzinfo=None))
print local
print tz.localize(local.replace(tzinfo=None))