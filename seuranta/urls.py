from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.views import obtain_auth_token
from seuranta.api import views as api_views


urlpatterns = patterns(
    'seuranta.views',
    url(
        r'^$',
        TemplateView.as_view(template_name='seuranta/home.html'),
        name='seuranta_home'
    ),
    url(
        r'^dashboard/?$',
        TemplateView.as_view(template_name='seuranta/dashboard.html'),
        name='seuranta_dashboard'
    ),
    url(
        r'media/seuranta/maps/(?P<publisher>[^/]+)/'
        r'(?P<hash>[-0-9a-zA-Z_])/(?P<pk>(?P=hash)[-0-9a-zA-Z_]{21})',
        'admin_map_image',
        name='seuranta_admin_map_image',
    ),
)

urlpatterns += patterns(
    'seuranta.api',
    url(
        r'^api/time/?$',
        api_views.time_view,
        name='seuranta_api_time'
    ),
    url(
        r'^api/auth_token/obtain/?$',
        obtain_auth_token,
        name='seuranta_api_auth_token_obtain'
    ),
    url(
        r'^api/auth_token/destroy/?$',
        api_views.destroy_auth_token,
        name='seuranta_api_auth_token_destroy'
    ),
    url(
        r'^api/competition/?$',
        api_views.CompetitionListView.as_view(),
        name='seuranta_api_competitions'
    ),
    url(
        r'^api/competition/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        api_views.competition,
        name='seuranta_api_competition'
    ),
    url(
        r'^api/map/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        api_views.competition_map,
        name='seuranta_api_competition_map'
    ),
    url(
        r'^api/map/(?P<pk>[-a-zA-Z0-9_]{22})\.jpg$',
        api_views.download_map,
        name='seuranta_api_download_map'
    ),
    url(
        r'^api/competitor/?$',
        api_views.competitors,
        name='seuranta_api_competitors'
    ),
    url(
        r'^api/competitor/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        api_views.competitor,
        name='seuranta_api_competitor_detail'
    ),
    url(
        r'^api/competitor_token/obtain/?$',
        api_views.obtain_competitor_token,
        name='seuranta_api_obtain_competitor_token'
    ),
    url(
        r'^api/competitor_token/destroy/?$',
        api_views.destroy_competitor_token,
        name='seuranta_api_destroy_competitor_detail'
    ),
    url(
        r'^api/route/?$',
        api_views.routes,
        name='seuranta_api_routes'
    ),
    url(
        r'^api/route/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        api_views.competitor_route,
        name='seuranta_api_competitor_route'
    ),
    # url(
    #    r'^api/location/post'
    #    api_views.RouteListView.as_view(),
    #    name='seuranta_api_route_list'
    # ),
)

