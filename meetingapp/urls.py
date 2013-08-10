from django.conf.urls import patterns, include, url
from data import views
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^create/$', views.create),
    (r'^signup/$', views.signup),
    (r'^login/$', views.login),
    (r'^logout/$', views.logout),
    (r'^home/$', views.home),
    (r'^profile/$', views.profile),
    (r'^contacts/$', views.contacts),
    (r'^meeting/.{15}$', views.meeting),
    (r'^verify/.{25}$', views.verify),
    (r'^vote/$', views.vote),
    (r'^invite/$', views.invite),
    (r'^settings/$', views.settings),
    (r'^addorganizer/$', views.addorganizer),
    (r'^attachorg/$', views.attachorg),
    (r'^managemembers/$', views.managemembers),
    (r'^orgs/.{22}$', views.orgpage),
    (r'^profile/.{21}$', views.profpage),
    (r'^setinterview/$', views.setinterview),
    (r'^setchat/$', views.setchat),
    (r'^setnormal/$', views.setnormal),
    (r'^intersub/$', views.intersub),
    (r'^chatonline/$', views.chatonline),
    (r'^chatbanlist/$', views.chatbanlist),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),

    # Examples:
    # url(r'^$', 'meetingapp.views.home', name='home'),
    # url(r'^meetingapp/', include('meetingapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
