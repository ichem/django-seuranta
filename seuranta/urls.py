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

	url(r'^(?P<publisher>[^/]+)/?$',
		'user_home',
        name='seuranta_user_home'
	),

	url(r'^(?P<publisher>[^/]+)/(?P<slug>[-a-zA-Z0-9_]+)\.html$',
		'race_view',
        name='seuranta_race'
	),

	url(r'^api/v1/(?P<action>.*)/?$',
		'api_v1',
        name='seuranta_api'
	),
	
	url(r'^api/rerun/', 'rerun_data'),
    url(r'^api/rerun/map$', 'rerun_map'),
    url(r'^api/rerun/init\.php$', 'rerun_init'),
    url(r'^api/rerun/time\.php$', 'rerun_time'),
)
