from django.conf.urls import patterns, url

urlpatterns = patterns('seuranta.views',
	url(r'^$',
		"home",
	),

	url(r'^dashboard/?$',
		"dashboard",
	),

	url(r'^web_tracker/?$',
	    "tracker",
	),

    url(r'^races/?$',
        "races_browse",
    ),

	url(r'^races/(?P<uuid>[0-9a-zA-Z_-]+)/?$',
		"races_view",
	),

	url(r'^api/?$',
		"api",
	),
)
