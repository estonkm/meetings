from django.conf.urls import patterns, include, url
from data import views
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', views.home),
    (r'^meeting/$', views.meeting),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
    # Examples:
    # url(r'^$', 'meetingapp.views.home', name='home'),
    # url(r'^meetingapp/', include('meetingapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
