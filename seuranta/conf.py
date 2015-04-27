from django.conf import settings
from appconf import AppConf


class SeurantaConf(AppConf):
    ACCESS_CODE_LENGTH = 5

    class Meta:
        prefix = 'seuranta'