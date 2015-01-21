from django.conf.urls import patterns, url
from seuranta.api import v2


urlpatterns = patterns(
    'seuranta.views',
    url(
        r'^$',
        'home',
        name='seuranta_home'),
    url(
        r'^tracker/(?P<api_token>[-a-zA-Z0-9_]{22})?$',
        'tracker',
        name='seuranta_tracker'
    ),
    url(
        r'^(?P<publisher>(?!tracker|dashboard|api|rerun)[^/]+)/$',
        'user_home',
        name='seuranta_user_home'
    ),
    url(
        r'^(?P<publisher>[^/]+)/(?P<slug>[-a-zA-Z0-9_]+)\.html$',
        'race_view',
        name='seuranta_race'
    ),
)

urlpatterns += patterns(
    'seuranta.api.v1',
    url(
        r'^api/v1/(?P<action>.*)/?$',
        'api_v1',
        name='seuranta_api_v1'
    ),
)


urlpatterns += patterns(
    'seuranta.api.v2',
    url(
        r'^api/v2/competition/?$',
        v2.CompetitionListView.as_view(),
        name='seuranta_api_v2_competition_list'
    ),
    url(
        r'^api/v2/competition/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        v2.CompetitionDetailView.as_view(),
        name='seuranta_api_v2_competition_detail'
    ),
    url(
        r'^api/v2/map/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        v2.MapDetailView.as_view(),
        name='seuranta_api_v2_map_detail'
    ),
    url(
        r'^api/v2/map/(?P<pk>[-a-zA-Z0-9_]{22})\.jpg$',
        v2.download_map,
        name='seuranta_api_v2_map_download'
    ),
    url(
        r'^api/v2/competitor/?$',
        v2.CompetitorListView.as_view(),
        name='seuranta_api_v2_competitor_list'
    ),
    url(
        r'^api/v2/competitor/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        v2.CompetitorDetailView.as_view(),
        name='seuranta_api_v2_competitor_detail'
    ),
    url(
        r'^api/v2/route/?$',
        v2.RouteListView.as_view(),
        name='seuranta_api_v2_route_list'
    ),
    url(
        r'^api/v2/route/(?P<pk>[-a-zA-Z0-9_]{22})/?$',
        v2.RouteDetailView.as_view(),
        name='seuranta_api_v2_route_list'
    ),
)

urlpatterns += patterns(
    'seuranta.api.rerun',
    url(
        r'^api/rerun/time\.php$',
        'rerun_time',
        name='seuranta_rerun_time'
    ),
    url(
        r'^api/rerun/init\.php$',
        'rerun_init',
        name='seuranta_rerun_init'
    ),
    url(
        r'^api/rerun/$',
        'rerun_data',
        name='seuranta_rerun_data'
    ),
    url(
        r'^api/rerun/map$',
        'rerun_map',
        name='seuranta_rerun_map'
    ),
    url(
        r'^api/rerun/redirect/'
        r'(?P<publisher>[^/]+)/(?P<slug>[-a-zA-Z0-9_]+)$',
        'rerun_redirect',
        name='seuranta_rerun_redirect'
    ),
)
