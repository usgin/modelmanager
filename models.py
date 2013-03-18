from django.db import models
from django.conf import settings
from django.template.defaultfilters import slugify
from django.db.models.signals import pre_save, post_save, post_delete
#from django.dispatch import receiver
from uriconfigure import adjust_rewrite_rule, delete_rewrite_rule, update_related_rewrite_rules, RewriteRule
from os import path
from lxml import etree
import re

#--------------------------------------------------------------------------------------
# Function that gets the path for a uploaded files.
#     File path will be content-model-slug/version-number/filename            
#--------------------------------------------------------------------------------------
def get_file_path(instance, filename):
    return '%s/%s/%s' % (instance.content_model.folder_path(), instance.version, filename)
    
#--------------------------------------------------------------------------------------
# Function that strips HTML tags (except anchors) from strings         
#--------------------------------------------------------------------------------------
def removeTags(string_to_clean):
    return re.sub('</(?!a)[^>]*>|<[^/a][^>]*>|&nbsp;', '', string_to_clean)

#--------------------------------------------------------------------------------------
# This class represent specific USGIN content-models, which are built to convey
#     specific types of geoscience information.
#--------------------------------------------------------------------------------------
class ContentModel(models.Model):
    class Meta:
        ordering = ['title']    # Defines the order of any list of ContentModels
        
    # Define the class data members
    title = models.CharField(max_length=2500)
    label = models.CharField(max_length=2500, unique=True)
    description = models.TextField()
    discussion = models.TextField(blank=True)
    status = models.TextField(blank=True)
    rewrite_rule = models.OneToOneField(RewriteRule, null=True, blank=True)
    
    # Functions to return cleaned-up properties
    def cleaned_description(self):
        return removeTags(self.description)
        
    def cleaned_discussion(self):
        return removeTags(self.discussion)
        
    def cleaned_status(self):
        return removeTags(self.status)
    
    # Define the "display name" for an instance
    def __unicode__(self):
        return self.title
    
    # Define the folder path for an instance -- just a simplification of the title
    def folder_path(self):
        return slugify(self.title)
    
    # Simple pointer to the latest version of a instance
    def latest_version(self):
        if self.modelversion_set.count() > 0: return self.modelversion_set.latest('date_created')
        else: return None
    
    # Simply return the latest version number
    def latest_version_number(self):
        version = self.latest_version()
        if version: return version.version
        else: return None
    
    # The updated date for an instance is the last time that a version was created
    def date_updated(self):
        version = self.latest_version()
        if version is not None: return version.date_created
        else: return None
        
    # Return the updated date as an ISO-formatted string
    def iso_date_updated(self):
        updated = self.date_updated()
        if updated is not None: return updated.isoformat()
        else: return None
    
    # Return the absolute path to the latest version's XSD file
    def absolute_latest_xsd_path(self):
        version = self.latest_version()
        if version is not None: return self.latest_version().absolute_xsd_path()
        else: return None
    
    # Return the absolute path to the latest version's XLS file
    def absolute_latest_xls_path(self):
        version = self.latest_version()
        if version is not None: return self.latest_version().absolute_xls_path()
        else: return None
    
    # Provide a link to the latest version's XSD file
    def latest_xsd_link(self):
        version = self.latest_version()
        if version != None: return self.latest_version().xsd_link()
        else: return None
    latest_xsd_link.allow_tags = True
    
    # Provide a link to the latest version's XLS file
    def latest_xls_link(self):
        version = self.latest_version()
        if version != None: return self.latest_version().xls_link()
        else: return None
    latest_xls_link.allow_tags = True
    
    # Provide a URL for this ContentModel as HTML. Needs to be in sync with urls.py.
    def my_html(self):
        return '%s/contentmodel/%s.html' % (settings.BASE_URL.rstrip('/'), self.pk)
    
    # Provide a URL for this ContentModel as JSON. Needs to be in sync with urls.py.
    def my_json(self):
        return '%s/contentmodel/%s.json' % (settings.BASE_URL.rstrip('/'), self.pk)
    
    # Provide a URL for this ContentModel as Atom XML. Needs to be in sync with urls.py.
    def my_atom(self):
        return '%s/contentmodel/%s.xml' % (settings.BASE_URL.rstrip('/'), self.pk)
        
    # Return RegEx pattern for use in UriRegister module
    def stripped_regex(self):
        return "dataschema/%s/" % self.label
    
    def regex_pattern(self):
        return '^%s(\.[a-zA-Z]{3,4}|/)?$' % self.stripped_regex()
    
    # Provide this ContentModel's relative URI
    def relative_uri(self):
        return '/uri-gin/%s/%s' % (settings.URI_REGISTER_LABEL, self.stripped_regex())
    
    # Provide this ContentModel's absolute URI
    def absolute_uri(self):
        return '%s%s' % (settings.BASE_URL.rstrip('/'), self.relative_uri())
    
    # Return a link to this ContentModel's RewriteRule
    def rewrite_rule_link(self):
        return '<a href="/admin/uriredirect/rewriterule/%s">Edit Rule</a>' % self.rewrite_rule.pk
    rewrite_rule_link.allow_tags = True
        
    # Return the instance as a dictionary that can be easily converted to JSON
    #     Include a list of versions relevant to this content model
    def serialized(self):
        as_json = {
            'title': self.title,
            'uri': self.absolute_uri(),
            'description': self.description,
            'discussion': self.discussion,
            'status': self.status,
            'date_updated': self.iso_date_updated(),
            'versions': [ mv.serialized() for mv in self.modelversion_set.all() ]
        }        
        return as_json

#--------------------------------------------------------------------------------------
# This class represents a specific version of a particular content-model. 
#     A one-to-many relationship exists between ContentModels and ModelVersions. 
#--------------------------------------------------------------------------------------
class ModelVersion(models.Model):
    class Meta:
        ordering = ['version']    # Defines the order of any list of ModelVersions
        
    # Define the models data members
    content_model = models.ForeignKey('ContentModel')
    version = models.CharField(max_length=10)
    date_created = models.DateField(auto_now_add=True)
    xsd_file = models.FileField(upload_to=get_file_path)
    xls_file = models.FileField(upload_to=get_file_path)
    sample_wfs_request = models.CharField(max_length=2000, blank=True)
    rewrite_rule = models.OneToOneField(RewriteRule, null=True, blank=True)
    
    # Return the first-decimal, or "Major" version number. In the case of version 1.23 this would be 1.2
    def major_version(self):
        m = re.match('\d*\.\d{1}', self.version)
        if m: return m.group(0)
        else: return None
    
    # Define the "display name" for an instance
    def __unicode__(self):
        return '%s v. %s' % (self.content_model.title, self.version)
    
    # Define the absolute URI for this version -- it is simply the version number appended to the ContentModel.uri    
    def absolute_uri(self):
        return '%s/%s' % (self.content_model.absolute_uri().rstrip('/'), self.version)
    
    # Return just the base name of the XSD file without any associated file path
    def xsd_filename(self):
        return path.basename(self.xsd_file.name)
        
    # Return just the base name of the XLS file without any associated file path
    def xls_filename(self):
        return path.basename(self.xls_file.name)
    
    # Return an HTML anchor tag for the XSD file
    def xsd_link(self):
        return '<a href="%s">%s</a>' % (self.absolute_xsd_path(), self.xsd_filename())
    xsd_link.allow_tags = True    # This lets the admin interface show the anchor

    # Return an HTML anchor tag for the XLS file
    def xls_link(self):
        return '<a href="%s">%s</a>' % (self.absolute_xls_path(), self.xls_filename())
    xls_link.allow_tags = True    # This lets the admin interface show the anchor
    
    # Return absolute URL for XSD file
    def absolute_xsd_path(self):
        return '%s/%s' % (settings.BASE_URL.rstrip('/'), self.xsd_file.url.lstrip('/'))
            
    # Return absolute URL for XLS file
    def absolute_xls_path(self):
        return '%s/%s' % (settings.BASE_URL.rstrip('/'), self.xls_file.url.lstrip('/'))
    
    # Return RegEx pattern for use in UriRegister module
    def regex_pattern(self):
        return '^%s/%s(\.[a-zA-Z]{3,4}|/)?$' % (self.content_model.stripped_regex().rstrip('/'), self.version)
    
    # Return a link to this ModelVersion's RewriteRule
    def rewrite_rule_link(self):
        return '<a href="/admin/uriredirect/rewriterule/%s">Edit Rule</a>' % self.rewrite_rule.pk
    rewrite_rule_link.allow_tags = True
    
    # Return the created date in ISO format
    def iso_date_created(self):
        return self.date_created.isoformat()
    
    # Return an lxml.etree.XMLSchema validator
    def schema_validator(self):
        # I don't know why this isn't working: schema_file = self.xsd_file.open()
        schema_file = open(self.xsd_file.path, 'r')
        schema_doc = etree.parse(schema_file)
        schema = etree.XMLSchema(schema_doc)
        return schema
    
    # Return the instance as a dictionary that can be easily converted to JSON.
    #     Contains URLs to directly download files 
    def serialized(self):
        as_json = {
            'uri': self.absolute_uri(),
            'version': self.version,
            'date_created': self.date_created.isoformat(),
            'xsd_file_path': self.absolute_xsd_path(),
            'xls_file_path': self.absolute_xls_path(),
            'sample_wfs_request': self.sample_wfs_request
        }        
        return as_json
        
#--------------------------------------------------------------------------------------
# Register a function to fire before ModelVersion and ContentModel objects are saved
#--------------------------------------------------------------------------------------        
pre_save.connect(adjust_rewrite_rule, sender=ModelVersion)
pre_save.connect(adjust_rewrite_rule, sender=ContentModel)

#--------------------------------------------------------------------------------------
# Register a function to fire after ModelVersion and ContentModel objects are saved
#--------------------------------------------------------------------------------------        
post_save.connect(update_related_rewrite_rules, sender=ModelVersion)
post_save.connect(update_related_rewrite_rules, sender=ContentModel)

#--------------------------------------------------------------------------------------
# Register a function to fire when ModelVersion and ContentModel objects are deleted
#--------------------------------------------------------------------------------------    
post_delete.connect(delete_rewrite_rule, sender=ModelVersion)
post_delete.connect(delete_rewrite_rule, sender=ContentModel)