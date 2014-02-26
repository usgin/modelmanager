from django.conf.urls import patterns, url

urlpatterns = patterns('modelmanager.validation.validators',

  # Validation form, and form submission
  url('^wfs$', 'validate_wfs_form'),
  url('^cm$', 'validate_cm_form'),
  url('^dl_csv$', 'download_csv')
)