from django.conf.urls import patterns, url

urlpatterns = patterns('seuranta.views',
	url(r'^$',
		'home',
        name='seuranta_home'
	),

	url(r'^dashboard/?$',
		'dashboard',
        name='seuranta_dashboard'
	),

	url(r'^tracker/(?P<uuid>[-a-zA-Z0-9_]+)?$',
	    'tracker',
        name='seuranta_tracker'
	),

	url(r'^api/v1/(?P<action>.*)/?$',
		'api_v1',
        name='seuranta_api_v1'
	),

	url(r'^rerun/$', 'rerun_data', name='seuranta_rerun_data'),
    url(r'^rerun/map$', 'rerun_map', name='seuranta_rerun_map'),
    url(r'^rerun/init\.php$', 'rerun_init', name='seuranta_rerun_init'),
    url(r'^rerun/time\.php$', 'rerun_time', name='seuranta_rerun_time'),

	url(r'^(?P<publisher>(?!tracker|dashboard|api|rerun)[^/]+)/$',
		'user_home',
        name='seuranta_user_home'
	),

	url(r'^(?P<publisher>[^/]+)/(?P<slug>[-a-zA-Z0-9_]+)\.html$',
		'race_view',
        name='seuranta_race'
	),

	url(r'^(?P<publisher>[^/]+)/(?P<slug>[-a-zA-Z0-9_]+)/rerun$',
		'race_rerun_view',
        name='seuranta_rerun'
	),
)
