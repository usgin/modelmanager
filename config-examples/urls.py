from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    
    # All URI redirection occurs at /uri-gin/ URLs
    url(r'^uri-gin/', include('uriredirect.urls')),
    
    # All validation occurs at /validate/ URLs
    url(r'^validate/', include('modelmanager.validation.urls')),
)

# Append urlpatterns from modelmanager.contentmodels
from modelmanager.urls import urlpatterns as cm_urls
urlpatterns += cm_urls
