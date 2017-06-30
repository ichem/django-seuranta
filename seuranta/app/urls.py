from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from seuranta.views import admin_map_image
from seuranta.app import views

admin.autodiscover()

urlpatterns = [
    url(
        r'^$',
        TemplateView.as_view(template_name='seuranta/home.html'),
        name='seuranta_home'
    ),
    url(r'^dashbord/?$',
        views.own_competitions,
        name='seuranta_dashboard'
    ),
    url(r'^create_competition/?$',
        views.create_competition,
        name='seuranta_create_competition'
    ),
    url(
        r'^tracker/?$',
        TemplateView.as_view(template_name='seuranta/tracker.html'),
        name='seuranta_tracker'
    ),
    url(
        r'^watch/?$',
        TemplateView.as_view(template_name='seuranta/watch.html'),
        name='seuranta_list_competitions'
    ),
    url(
        r'^watch/(?P<competition_id>[-0-9a-zA-Z_]{11})/?$',
        TemplateView.as_view(template_name='seuranta/race_viewer.html'),
        name='seuranta_race'
    ),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^api/', include('seuranta.api.urls')),
    # Django admin specifics
    url(r'^admin/', include(admin.site.urls)),
    url(
        r'^media/seuranta/maps/(?P<publisher>[^/]+)/'
        r'(?P<hash>[-0-9a-zA-Z_])/(?P<hash2>[-0-9a-zA-Z_])/'
        r'(?P<pk>(?P=hash)(?P=hash2)[-0-9a-zA-Z_]{9})',
        admin_map_image,
        name='seuranta_admin_map_image',
    ),
]
