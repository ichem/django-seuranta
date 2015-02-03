from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^api/', include('seuranta.api.urls')),

)

# Django admin specifics
urlpatterns += patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(
        r'^media/seuranta/maps/(?P<publisher>[^/]+)/'
        r'(?P<hash>[-0-9a-zA-Z_])/(?P<hash2>[-0-9a-zA-Z_])/'
        r'(?P<pk>(?P=hash)(?P=hash2)[-0-9a-zA-Z_]{20})',
        'seuranta.views.admin_map_image',
        name='seuranta_admin_map_image',
    ),
)