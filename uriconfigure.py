from uriredirect.models import UriRegister, RewriteRule, MediaType, AcceptMapping
from django.conf import settings

#--------------------------------------------------------------------------------------
# Utility function to retrieve the default URI register
#--------------------------------------------------------------------------------------
def get_default_register():
  # Attempt to retrieve the default register defined in the project's settings
  try:
    return UriRegister.objects.get(label=settings.URI_REGISTER_LABEL)
  
  # This exception is thrown if the register does not yet exist. Create it and return it.
  except UriRegister.DoesNotExist:    
    return UriRegister.objects.create(
        label=settings.URI_REGISTER_LABEL, 
        url=settings.URI_REGISTER_URL, 
        can_be_resolved=True
      )

#--------------------------------------------------------------------------------------
# Utility function to retrieve specific media types
#--------------------------------------------------------------------------------------
def get_media_type(kwargs):
  # Attempt to locate the requested media type
  try:    
    return MediaType.objects.get(**kwargs)
  
  # This exception indicates that the media type doesn't yet exist. Create and return it.
  except MediaType.DoesNotExist:    
    return MediaType.objects.create(**kwargs)
  
#--------------------------------------------------------------------------------------
# Functions to get the four needed media types needed within the module
#--------------------------------------------------------------------------------------
def XSD_MEDIA():
  return get_media_type({
      "mime_type": "application/xml",
      "file_extension": ".xsd"
    })
def XLS_MEDIA(): 
  return get_media_type({
      "mime_type": "application/vnd.ms-excel",
      "file_extension": ".xls"
    })
def HTML_MEDIA():
  return get_media_type({
      "mime_type": "text/html",
      "file_extension": ".html"
    })
def JSON_MEDIA():
  return get_media_type({
      "mime_type": "text/json",
      "file_extension": ".json"
    })

#--------------------------------------------------------------------------------------
# Function to define RewriteRule attributes from an object
#   instance is a ModelVersion or ContentModel object  
#--------------------------------------------------------------------------------------
def create_rule_attribs(instance):
  return {
    "register": get_default_register(),
    "label": instance.__unicode__(),
    "description": "Redirection rule for %s" % instance.__unicode__(),
    "pattern": instance.regex_pattern()
  }

#--------------------------------------------------------------------------------------
# Function to create a RewriteRule
#--------------------------------------------------------------------------------------
def create_rewrite_rule(instance, class_name):
  # Create the attributes that will define the RewriteRule
  rule_attribs = create_rule_attribs(instance)
  
  # Create the RewriteRule
  rule = RewriteRule.objects.create(**rule_attribs)
  
  # Associate the RewriteRule with this object
  instance.rewrite_rule = rule
  
  # Configure AcceptMappings for this RewriteRule
  configure_rule_mappings(instance, rule, class_name)
  
  # Return the rule
  return rule
  
#--------------------------------------------------------------------------------------
# Function to update a RewriteRule
#--------------------------------------------------------------------------------------
def update_rewrite_rule(instance, rule, class_name):
  # Create the attributes that will define the RewriteRule
  rule_attribs = create_rule_attribs(instance)
  
  # Add the rule's pk to the attributes hash, allowing it to be used to update
  rule_attribs["pk"] = rule.pk
  
  # Update the rule
  rule = RewriteRule(**rule_attribs)
  rule.save()
  
  # Configure AcceptMappings for this RewriteRule
  configure_rule_mappings(instance, rule, class_name)
  
#--------------------------------------------------------------------------------------
# Function to configure AcceptMappings for a RewriteRule
#--------------------------------------------------------------------------------------
def configure_rule_mappings(instance, rule, class_name):
  # Configure the AcceptMappings for a ModelVersion's RewriteRule.
  if class_name is "ModelVersion":
    configure_version_mappings(instance, rule)
  
  # Configure the AcceptMappings for a ContentModel's RewriteRule.
  elif class_name is "ContentModel":     
    configure_model_mappings(instance, rule)

#--------------------------------------------------------------------------------------
# This function creates or updates an AcceptMapping, given --
#   rewriterule: a RewriteRule to which the AcceptMapping pertains
#   url: the URL to which the AcceptMapping should redirect
#   mediatype: the MediaType which is represented by the AcceptMapping
#--------------------------------------------------------------------------------------
def configure_mapping(rewriterule, url, mediatype):
  # Setup the attributes that will define the AcceptMapping
  mapping_attribs = {
    "rewrite_rule": rewriterule,
    "media_type": mediatype,
    "redirect_to": url
  }
  
  # Look for an existing AcceptMapping associated with this RewriteRule and having
  #   the correct media_type. If there is one, put its index into the attributes in
  #   order to force an update of the existing AcceptMapping.
  try:    
    mapping_attribs["pk"] = rewriterule.acceptmapping_set.get(media_type=mediatype).pk
  
  # Don't need to adjust any attributes if there is no AcceptMapping yet.
  except AcceptMapping.DoesNotExist:    
    pass
    
  # Create a new one or update an existing AcceptMapping
  finally:
    mapping = AcceptMapping(**mapping_attribs)
    mapping.save()
    
#--------------------------------------------------------------------------------------
# Function to create AcceptMappings for a ModelVersion
#--------------------------------------------------------------------------------------
def configure_version_mappings(instance, rule):
  configure_mapping(rule, instance.absolute_xls_path(), XLS_MEDIA())
  configure_mapping(rule, instance.absolute_xsd_path(), XSD_MEDIA())
  configure_mapping(rule, instance.content_model.my_html(), HTML_MEDIA())
  configure_mapping(rule, instance.content_model.my_json(), JSON_MEDIA())
  
#--------------------------------------------------------------------------------------
# Function to create AcceptMappings for a ContentModel
#--------------------------------------------------------------------------------------
def configure_model_mappings(instance, rule):
  # When you first create a ContentModel, the instance does not yet have an ID assigned.
  #    instance.my_html() and my_json() return None, and AcceptMappings are incorrect.
  configure_mapping(rule, instance.my_html(), HTML_MEDIA())
  configure_mapping(rule, instance.my_json(), JSON_MEDIA())
  
  # File mappings depend on there being a ModelVersion in the set
  if instance.latest_version() is not None:    
    configure_mapping(rule, instance.absolute_latest_xls_path(), XLS_MEDIA())
    configure_mapping(rule, instance.absolute_latest_xsd_path(), XSD_MEDIA())
  
#--------------------------------------------------------------------------------------
# This function manages RewriteRules defined by the uriredirect module.
#   The function is called before a ModelVersion or ContentModel is saved. 
#   It is registered in models.py.
#   sender is a reference to the class that is being saved
#   instance is the object that is being saved
#--------------------------------------------------------------------------------------
def adjust_rewrite_rule(sender, instance, **kwargs):
  # Look for a RewriteRule associated with this instance
  rule = instance.rewrite_rule
  
  # Create one if it doesn't already exist, update it if it does
  class_name = sender.__name__
  if rule is None: rule = create_rewrite_rule(instance, class_name)
  else: update_rewrite_rule(instance, rule, class_name)

#--------------------------------------------------------------------------------------
# This function updates RewriteRules that pertain to objects related to the 
#   instance that has been saved. The function is registered in models.py and is 
#   called after the object is saved
#--------------------------------------------------------------------------------------
def update_related_rewrite_rules(sender, instance, **kwargs):
  # Find the class name of the object being saved
  class_name = sender.__name__
  
  # Saving a ModelVersion may change the latest version of the ContentModel,
  #   which effects the ContentModel's RewriteRule.
  if class_name is "ModelVersion":    
    update_rewrite_rule(instance.content_model, instance.content_model.rewrite_rule, "ContentModel")
  
  # Changes to a ContentModel can affect ModelVersion's RewriteRules (i.e. changing the label).
  elif class_name is "ContentModel":    
    for version in instance.modelversion_set.all(): update_rewrite_rule(version, version.rewrite_rule, "ModelVersion")

#--------------------------------------------------------------------------------------
# This function deletes a RewriteRule when a ModelVersion or ContentModel is deleted
#   The function is registered in models.py and called after the object is deleted.
#   sender is a reference to the class of object being deleted
#   instance is the object that was deleted
#--------------------------------------------------------------------------------------
def delete_rewrite_rule(sender, instance, **kwargs):
  # Simply delete the RewriteRule, if it exists!
  if instance.rewrite_rule != None:
    instance.rewrite_rule.delete()
  
