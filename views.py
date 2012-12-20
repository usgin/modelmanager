from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from models import ContentModel
from datetime import datetime
import json

#--------------------------------------------------------------------------------------
# Expose all the available ContentModels
#--------------------------------------------------------------------------------------
def get_all_models(request, extension):
  all_models = ContentModel.objects.all()
  return view_models(all_models, extension)
  
#--------------------------------------------------------------------------------------
# Expose a single ContentModel
#--------------------------------------------------------------------------------------
def get_model(request, id, extension):
  contentmodels = ContentModel.objects.filter(pk=id)
  if not contentmodels: raise Http404
  return view_models(contentmodels, extension)
  
#--------------------------------------------------------------------------------------
# Choose the appropriate format to expose based on the requested extension
#--------------------------------------------------------------------------------------
def view_models(contentmodels, extension):
  if extension == 'json': return as_json(contentmodels)
  elif extension == 'xml': return as_atom(contentmodels)
  elif extension == 'drupal': return fer_drupal(contentmodels)
  else: return as_html(contentmodels)
  
#--------------------------------------------------------------------------------------
# Convert a set of ContentModel instances to JSON and send as an HttpResponse
#--------------------------------------------------------------------------------------
def as_json(contentmodels):
  data = [ cm.serialized() for cm in contentmodels ]
  return HttpResponse(json.dumps(data), mimetype='application/json')
  
#--------------------------------------------------------------------------------------
# Convert a set of ContentModel instances to HTML and send as an HttpResponse
#--------------------------------------------------------------------------------------
def as_html(contentmodels):
  return render_to_response('contentmodels.html', { 'contentmodels': contentmodels })

#--------------------------------------------------------------------------------------
# Convert a set of ContentModel instances to XML (Atom) and send as an HttpResponse
#--------------------------------------------------------------------------------------
def as_atom(contentmodels):
  return render_to_response(
      'contentmodels.xml', 
      { 'feed': AtomFeed(contentmodels=contentmodels), 'contentmodels': contentmodels },
      mimetype="application/xml"
    )
    
#--------------------------------------------------------------------------------------
# Convert a set of ContentModel instances to XML (fer Drupal) and send as an HttpResponse
#--------------------------------------------------------------------------------------
def fer_drupal(contentmodels):
  return render_to_response(
      'ferDrupal.xml', { 'contentmodels': contentmodels }, mimetype="application/xml"
    )

#--------------------------------------------------------------------------------------
# Class for generating an Atom Feed. Default values as shown, can be adjusted by 
#   keyword-args on creation.
#--------------------------------------------------------------------------------------
class AtomFeed(object):
  # These are default values for feed attributes
  title = "Content Models"
  subtitle = "USGIN Content Models Atom Feed"
  url = "http://schemas.usgin.org/contentmodels.xml"
  id = "http://schemas.usgin.org/contentmodels.xml"
  date = datetime.now().isoformat()
  author_name = "Ryan Clark"
  author_email = "metadata@usgin.org"
  contentmodels = ContentModel.objects.all()
  
  # Constructor function. Map kwargs to this instance to overwrite defaults
  def __init__(self, **kwargs):
    # Loop through arguments passed in
    for arg in kwargs:
      # Assign them to this instance, overwriting default values
      setattr(self, arg, kwargs[arg])
      
    # Set date and id
    self.set_date()
    self.set_id_and_url()
  
  # Function to set the feed's updated date based on the ContentModels passed in
  def set_date(self):
    # Count the number of ContentModels that were passed in
    number_of_models = self.contentmodels.count()
    
    # There is more than one ContentModel
    if number_of_models > 1:
      # Sort the ContentModels by date
      sortable = list(self.contentmodels)
      sortable.sort(key=lambda cm: cm.date_updated())
      # Set the feed's date to the most recent ContentModel's updated date
      self.date = sortable[len(sortable)-1].iso_date_updated() 
    
    # There is one ContentModel
    elif number_of_models == 1:
      # This ContentModel's date is what we want
      self.date = self.contentmodels[0].iso_date_updated()
  
  # Function to set the feed's id and url    
  def set_id_and_url(self):
    # Use the default values unless this is a Feed containing only one ContenModel
    if self.contentmodels.count() == 1:
      # Set the feed's id and url to that of the passed in ContentModel
      self.url = self.contentmodels[0].my_atom()
      self.id = self.contentmodels[0].my_atom()
      
#--------------------------------------------------------------------------------------
# Homepage
#--------------------------------------------------------------------------------------
def homepage(req):
  def recent(cm):
    if cm.date_updated():
      return cm.date_updated()
    else:
      return datetime(1900,1,1)
  models = list(ContentModel.objects.all())
  models.sort(key=lambda cm: recent(cm), reverse=True)
  return render_to_response('home.html', { 'recent_models': models[:3] })
  
#--------------------------------------------------------------------------------------
# Model view page
#--------------------------------------------------------------------------------------
def models(req):
  return render_to_response('models.html', { 'contentmodels': ContentModel.objects.all() })
  