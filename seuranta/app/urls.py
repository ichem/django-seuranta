from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from seuranta.views import admin_map_image
admin.autodiscover()

urlpatterns = [
    url(
        r'^$',
        TemplateView.as_view(template_name='seuranta/home.html'),
        name='seuranta_home'
    ),
    url(
        r'^tracker/?$',
        TemplateView.as_view(template_name='seuranta/tracker.html'),
        name='seuranta_tracker'
    ),
    url(
        r'^watch/(?P<competition_id>[-0-9a-zA-Z_]{22})/?$',
        TemplateView.as_view(template_name='seuranta/race_viewer.html'),
        name='seuranta_map'
    ),
    url(r'^api/', include('seuranta.api.urls')),

    # Django admin specifics
    url(r'^admin/', include(admin.site.urls)),
    url(
        r'^media/seuranta/maps/(?P<publisher>[^/]+)/'
        r'(?P<hash>[-0-9a-zA-Z_])/(?P<hash2>[-0-9a-zA-Z_])/'
        r'(?P<pk>(?P=hash)(?P=hash2)[-0-9a-zA-Z_]{20})',
        admin_map_image,
        name='seuranta_admin_map_image',
    ),
]