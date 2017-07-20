from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from rest_framework.documentation import include_docs_urls
from seuranta.views import admin_map_image
from seuranta.app import views

admin.autodiscover()

urlpatterns = [
    url(
        r'^$',
        TemplateView.as_view(template_name='seuranta/home.html'),
        name='seuranta_home'
    ),
    url(
        r'^manifest.json$',
        TemplateView.as_view(template_name='seuranta/manifest.html'),
        name='seuranta_manifest'
    ),
    url(r'^dashboard/?$',
        views.own_competitions,
        name='seuranta_dashboard'
    ),
    url(r'^create_competition/?$',
        views.create_competition,
        name='seuranta_create_competition'
    ),
    url(r'^edit_competition/(?P<competition_id>[-0-9a-zA-Z_]{11})/?$',
        views.edit_competition,
        name='seuranta_edit_competition'
    ),
    url(r'^edit_map/(?P<competition_id>[-0-9a-zA-Z_]{11})/?$',
        views.edit_map,
        name='seuranta_edit_map'
    ),
    url(r'^edit_competitors/(?P<competition_id>[-0-9a-zA-Z_]{11})/?$',
        views.edit_competitors,
        name='seuranta_edit_competitors'
    ),
    url(
        r'^tracker/?$',
        TemplateView.as_view(template_name='seuranta/tracker.html'),
        name='seuranta_tracker'
    ),
    url(
        r'^watch/?$',
        views.list_competitions,
        name='seuranta_list_competitions'
    ),
    url(
        r'^watch/(?P<competition_id>[-0-9a-zA-Z_]{11})/?$',
        TemplateView.as_view(template_name='seuranta/race_viewer.html'),
        name='seuranta_race'
    ),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^api/', include('seuranta.api.urls')),
    url(r'^docs/', include_docs_urls(title='API Documentation')),
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
