from django.conf.urls import patterns, url, include
from rest_framework.authtoken.views import obtain_auth_token
from seuranta.api import views as api_views


urlpatterns = patterns(
    'seuranta.api.views',
    url(
        r'^time/?$',
        'get_time',
        name='seuranta_api_time'
    ),
    url(
        r'^auth_token/obtain/?$',
        obtain_auth_token,
        name='seuranta_api_auth_token_obtain'
    ),
    url(
        r'^auth_token/destroy/?$',
        'destroy_auth_token',
        name='seuranta_api_auth_token_destroy'
    ),
    url(
        r'^competition/?$',
        'competitions',
        name='seuranta_api_competitions'
    ),
    url(
        r'^competition/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        'competition',
        name='seuranta_api_competition'
    ),
    url(
        r'^map/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        'competition_map',
        name='seuranta_api_competition_map'
    ),
    url(
        r'^map/(?P<pk>[-a-zA-Z0-9_]{22})\.jpg$',
        'download_map',
        name='seuranta_api_competition_map_download'
    ),
    url(
        r'^competitor/?$',
        'competitors',
        name='seuranta_api_competitors'
    ),
    url(
        r'^competitor/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        'competitor',
        name='seuranta_api_competitor_detail'
    ),
    url(
        r'^competitor_token/obtain/?$',
        'obtain_competitor_token',
        name='seuranta_api_obtain_competitor_token'
    ),
    url(
        r'^competitor_token/destroy/?$',
        'destroy_competitor_token',
        name='seuranta_api_destroy_competitor_token'
    ),
    url(
        r'^route/?$',
        'routes',
        name='seuranta_api_routes'
    ),
    url(
        r'^route/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        'competitor_route',
        name='seuranta_api_competitor_route'
    ),
    # url(
    #    r'^location/post'
    #    'post_location_view',
    #    name='seuranta_api_route_list'
    # ),
)

