from django.conf.urls import patterns, url

urlpatterns = patterns('seuranta.views',
	url(r'^$',
		"home",
	),

	url(r'^web_tracker/(?P<uuid>[-a-zA-Z0-9_]+)?$',
	    "tracker",
	),

	url(r'^race/(?P<publisher>[^/]+)/(?P<slug>[-a-zA-Z0-9_]+)\.html$',
		"race_view",
	),

	url(r'^api/(?P<action>.*)/?$',
		"api",
	),
	
	url(r'^rerun/$', "rerun_data"),
	url(r'^rerun/map$', "rerun_map"),
	url(r'^rerun/init\.php$', "rerun_init"),
	url(r'^rerun/time\.php$', "rerun_time"),
)
