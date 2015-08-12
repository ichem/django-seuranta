from django.conf.urls import url
from rest_framework.authtoken.views import obtain_auth_token
from seuranta.api import views


urlpatterns = [
    url(
        r'^time/?$',
        views.get_time,
        name='seuranta_api_time'
    ),
    url(
        r'^auth_token/obtain/?$',
        obtain_auth_token,
        name='seuranta_api_auth_token_obtain'
    ),
    url(
        r'^auth_token/destroy/?$',
        views.destroy_auth_token,
        name='seuranta_api_auth_token_destroy'
    ),
    url(
        r'^competition/?$',
        views.competitions_view,
        name='seuranta_api_competitions'
    ),
    url(
        r'^competition/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        views.competition_view,
        name='seuranta_api_competition'
    ),
    url(
        r'^map/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        views.competition_map_view,
        name='seuranta_api_competition_map'
    ),
    url(
        r'^map/(?P<pk>[-a-zA-Z0-9_]{22})\.jpg$',
        views.download_map,
        name='seuranta_api_competition_map_download'
    ),
    url(
        r'^competitor/?$',
        views.competitors_view,
        name='seuranta_api_competitors'
    ),
    url(
        r'^competitor/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        views.competitor_view,
        name='seuranta_api_competitor'
    ),
    url(
        r'^competitor_token/obtain/?$',
        views.obtain_competitor_token,
        name='seuranta_api_obtain_competitor_token'
    ),
    url(
        r'^competitor_token/destroy/?$',
        views.destroy_competitor_token,
        name='seuranta_api_destroy_competitor_token'
    ),
    url(
        r'^route/?$',
        views.routes_view,
        name='seuranta_api_routes'
    ),
    url(
        r'^route/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        views.competitor_route_view,
        name='seuranta_api_competitor_route'
    ),
]

