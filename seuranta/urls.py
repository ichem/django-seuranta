from django.conf.urls import patterns, url

urlpatterns = patterns('seuranta.views',
	url(r'^$',
		"home",
	),

	url(r'^dashboard/?$',
		"dashboard",
	),

	url(r'^dashboard/race/(?P<uuid>[0-9a-zA-Z_-]+)/?$',
		"dashboard_edit_race",
	),

	url(r'^web_tracker/?$',
	    "tracker",
	),

	url(r'^race/(?P<uuid>[0-9a-zA-Z_-]+)/?$',
		"race_view",
	),

	url(r'^api/(?P<action>.*)/?$',
		"api",
	),
)
