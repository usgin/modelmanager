from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('modelmanager.views',

                       # Get all the ContentModels as JSON or HTML
                       url(r'^contentmodels\.(?P<extension>json|html|xml|drupal)$', 'get_all_models'),

                       # Get a single ContentModel as JSON or HTML
                       url(r'^contentmodel/(?P<id>\d*)\.(?P<extension>json|html|xml|drupal)$', 'get_model'),

                       # Get a FeatureCatalogue for a particular ModelVersion
                       url(r'^featurecatalog/(?P<id>\d*)\.xml', 'get_feature_catalog'),

                       # Homepage
                       url(r'^home/$', 'homepage'),

                       # Model viewing page
                       url(r'^models/$', 'models'),

                       # Tools page
                       url(r'^tools/$', 'tools'),

                       # Swagger documentation
                       url(r'^docs/', 'swaggerui'),
                       url(r'^swagger/(?P<path>.*)', 'swagger')
)

# Serve static files
if settings.DEBUG:
    urlpatterns += patterns('',
                            url(r'^files/(?P<path>.*)$', 'django.views.static.serve',
                                {'document_root': settings.MEDIA_ROOT}),
    )
