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
    cleaned = re.sub('</(?!a)[^>]*>|<[^/a][^>]*>', '', string_to_clean)
    return re.sub('&nbsp;', ' ', cleaned)

def add_target_to_anchors(string_to_fix, target="_blank"):
    """Given arbitrary string, find <a> tags and add target attributes"""
    pattern = re.compile("<a(?P<attributes>.*?)>")
    
    def repl_func(matchobj):
        pattern = re.compile("target=['\"].+?['\"]")
        attributes = matchobj.group("attributes")
        if pattern.search(attributes):
            return "<a%s>" % re.sub(pattern, "target='%s'" % target, attributes)
        else:
            return "<a%s target='%s'>" % (attributes, target)
    
    return re.sub(pattern, repl_func, string_to_fix)    
 
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
    
    # Construct the link for the nice-looking HTML for a particular model
    def my_pretty_html(self):
        return "%s/models/#%s" % (settings.BASE_URL.rstrip("/"), self.label)
    
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
    
    # Return a discussion text where <a> tags have been given target="_blank" attributes
    def discussion_for_drupal(self):
        return add_target_to_anchors(self.cleaned_discussion())
    
    # Return status text where <a> tags have been given target="_blank" attributes
    def status_for_drupal(self):
        return add_target_to_anchors(self.cleaned_status())
    
    # Return description text where <a> tags have been given target="_blank" attributes
    def description_for_drupal(self):
        return add_target_to_anchors(self.cleaned_description())
    
    # Return the most recent three versions, most recent first
    def recent_versions(self):
        return self.modelversion_set.order_by("-date_created")[:3]
    
    # Return the instance as a dictionary that can be easily converted to JSON
    #     Include a list of versions relevant to this content model
    def serialized(self):
        as_json = {
            'title': self.title,
            'uri': self.absolute_uri(),
            'label': self.label,
            'description': self.description,
            'discussion': self.discussion,
            'status': self.status,
            'date_updated': self.iso_date_updated(),
            'versions': [ mv.serialized() for mv in self.modelversion_set.all() ]
        }        
        return as_json

    # Return the layer name that should be used for this model
    def layer_name(self):
        return self.latest_version().type_details().layername

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
    sld_file = models.FileField(upload_to=get_file_path, blank=True)
    lyr_file = models.FileField(upload_to=get_file_path, blank=True)
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

    # Return just the base name of the SLD file without any associated file path
    def sld_filename(self):
        if self.sld_file:
            return path.basename(self.sld_file.name)

    # Return just the base name of the LYR file without any associated file path
    def lyr_filename(self):
        if self.lyr_file:
            return path.basename(self.lyr_file.name)

    # Return absolute URL for XSD file
    def absolute_xsd_path(self):
        return '%s/%s' % (settings.BASE_URL.rstrip('/'), self.xsd_file.url.lstrip('/'))

    # Return absolute URL for XLS file
    def absolute_xls_path(self):
        return '%s/%s' % (settings.BASE_URL.rstrip('/'), self.xls_file.url.lstrip('/'))

    # Return absolute URL for SLD file
    def absolute_sld_path(self):
        if self.sld_file:
            return '%s/%s' % (settings.BASE_URL.rstrip('/'), self.sld_file.url.lstrip('/'))

    # Return absolute URL for LYR file
    def absolute_lyr_path(self):
        if self.lyr_file:
            return '%s/%s' % (settings.BASE_URL.rstrip('/'), self.lyr_file.url.lstrip('/'))

    # Return an HTML anchor tag for the XSD file
    def xsd_link(self):
        return '<a href="%s">%s</a>' % (self.absolute_xsd_path(), self.xsd_filename())
    xsd_link.allow_tags = True    # This lets the admin interface show the anchor

    # Return an HTML anchor tag for the XLS file
    def xls_link(self):
        return '<a href="%s">%s</a>' % (self.absolute_xls_path(), self.xls_filename())
    xls_link.allow_tags = True    # This lets the admin interface show the anchor

    # Return an HTML anchor tag for the SLD file
    def sld_link(self):
        if self.sld_file:
            return '<a href="%s">%s</a>' % (self.absolute_sld_path(), self.sld_filename())
    sld_link.allow_tags = True    # This lets the admin interface show the anchor

    # Return an HTML anchor tag for the XSD file
    def lyr_link(self):
        if self.lyr_file:
            return '<a href="%s">%s</a>' % (self.absolute_lyr_path(), self.lyr_filename())
    lyr_link.allow_tags = True    # This lets the admin interface show the anchor
    
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
        class SchemaResolver(etree.Resolver):
            def resolve(self, url, id, context):
                schema_folder = path.join(
                    path.dirname(__file__), 
                    "validation", 
                    "schemas.opengis.net"
                )

                if url == "http://schemas.opengis.net/gml/3.1.1/base/gml.xsd":
                    that = path.join(
                        schema_folder,
                        "gml",
                        "3.1.1",
                        "base",
                        "gml.xsd"
                    )
                    return self.resolve_filename(that, context)
                else:    
                    return self.resolve_filename(url, context)
        
        parser = etree.XMLParser()
        parser.resolvers.add(SchemaResolver())
        
        # I don't know why this isn't working: schema_file = self.xsd_file.open()
        schema_file = open(self.xsd_file.path, 'r')
        schema_doc = etree.parse(schema_file, parser)
        try:
            schema = etree.XMLSchema(schema_doc)
        except etree.XMLSchemaParseError, err:
            print err
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
            'sample_wfs_request': self.sample_wfs_request,
            'field_info': self.field_info()
        }        
        return as_json

    # Parse a schema document to find details about fields
    def field_info(self):
        schema_file = open(self.xsd_file.path, 'r')
        schema = etree.parse(schema_file)
        ns = {
            "gco": "http://isotc211.org/2005/gco",
            "gmd": "http://isotc211.org/2005/gmd",
            "gmx": "http://isotc211.org/2005/gmx",
            "gss": "http://isotc211.org/2005/gss",
            "gfc": "http://isotc211.org/2005/gfc",
            "gsr": "http://isotc211.org/2005/gsr",
            "gts": "http://isotc211.org/2005/gts",
            "gml": "http://www.opengis.net/gml/3.2",
            "xlink": "http://www.w3.org/1999/xlink",
            "xs": "http://www.w3.org/2001/XMLSchema"
        }

        return [
            {
                "name": element.get("name"),
                "type": re.sub("^.*\:", "", element.get("type", next(iter(element.xpath("xs:simpleType/xs:restriction/@base", namespaces=ns)), ""))),
                "optional": True if element.get("minOccurs", "1") == "0" else False,
                "description": getattr(next(iter(element.xpath("xs:annotation/xs:documentation", namespaces=ns)), object()), "text", None)
            }
            for element in schema.xpath("//xs:sequence/xs:element", namespaces=ns)
        ]

    # Parse a schema document to determine the target namespace and type
    def type_details(self):
        schema_file = open(self.xsd_file.path, "r")
        schema = etree.parse(schema_file)
        ns = {
            "xs": "http://www.w3.org/2001/XMLSchema"
        }

        class type_details(object):
            namespace = next(iter(schema.xpath("/xs:schema/@targetNamespace", namespaces=ns)), "")
            typename = next(iter(schema.xpath("/xs:schema/xs:element/@type", namespaces=ns)), "").replace("Type", "")
            try:
                prefix = re.match("^(?P<prefix>.*):", typename).group("prefix")
                layername = re.search(":(?P<base>.*)$", typename).group("base")
            except:
                prefix = ""
                layername = ""
        return type_details()

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