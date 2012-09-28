from django.conf.urls.defaults import patterns, url
from django.conf import settings

urlpatterns = patterns(
    '',
    url(r'^$', 'dpaste.views.snippet_userlist', name='snippet_userlist'),
    url(r'^diff/$', 'dpaste.views.snippet_diff', name='snippet_diff'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{8})/$', 'dpaste.views.snippet_details',
        name='snippet_details'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{8})/delete/$',
        'dpaste.views.snippet_delete', name='snippet_delete'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{8})/merge/$',
        'dpaste.views.snippet_merge', name='snippet_merge'),
    url(r'^(?P<snippet_id>[a-zA-Z0-9]{8})/raw/$',
        'dpaste.views.snippet_details',
        {'template_name': 'dpaste/snippet_details_raw.html', 'is_raw': True},
        name='snippet_details_raw'),
)
