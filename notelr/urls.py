from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'enote.views.index', name='index'),
    # url(r'^notelr/', include('notelr.foo.urls')),
    url(r'^admin/doc/',
        include('django.contrib.admindocs.urls')),
    url(r'^admin/',
        include(admin.site.urls)),
    url(r'upload/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
    url(r'^auth$', 'enote.views.enote_oauth'),                    
    url(r'^auth/callback$',
        'enote.views.enote_oauth_callback'),
    url(r'^auth/logout$', 
        'enote.views.enote_logout'),
    url(r'^post/(?P<note_id>[0-9a-fA-F\-]+)$',
        'enote.views.blog_item', 
        name='blog_item'),
    url(r'^notebook/(?P<notebook_id>[0-9a-fA-F\-]+)$',
        'enote.views.notebook_page',
        name='notebook_page'),
    url(r'^(?P<username>[\w\.]+)\.rss$',
        'enote.views.rss_page',
        name='rss_page'),
    url(r'^watch/change', 'enote.views.change_callback',
        name='watch_change'),
    url(r'^(?P<username>[\w\.]+)$',
        'enote.views.blog_page',
        name='blog_page'),
)
