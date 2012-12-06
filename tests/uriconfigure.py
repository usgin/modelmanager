from django.test import TestCase
from django.conf import settings
from modelmanager.uriconfigure import *
from modelmanager.models import ContentModel, ModelVersion
from utils import create_dummy_files
from uriredirect.models import RewriteRule

def generate_content_model():
  """Function to generate an example ContentModel"""
  return ContentModel(
      title="Example Content Model",
      label="example",
      description="The example description",
      discussion="The example discussion",
      status="The example status"
    )
    
def generate_model_version(contentmodel):
  """Function to generate an example ModelVersion of the given ContentModel"""
  xsd, xls = create_dummy_files()
  return ModelVersion(
      content_model=contentmodel,
      version="1.0",
      xsd_file=xsd,
      xls_file=xls,
    )

class UriConfigureTestCase(TestCase):
  """Tests for the uriconfigure module, responsible for updating uriredirect models when adjustments to content models and versions are made"""
  
  def setUp(self):
    self.cm = generate_content_model()
    self.cm.save()
    self.mv = generate_model_version(self.cm)
    self.mv.save()
    
  def tearDown(self):
    pass
    
  def test_get_default_register(self):
    """get_default_register should always return the correct URI Register object"""
    self.assertEqual(get_default_register().label, settings.URI_REGISTER_LABEL)
  
  def test_get_media_type(self):
    """get_media_type should always return a MediaType object that has the properties passed into the function"""
    definition = { "mime_type": "text/html", "file_extension": "html" }
    media = get_media_type(definition)
    self.assertEqual(media.mime_type, definition['mime_type'])
    self.assertEqual(media.file_extension, definition['file_extension'])
    
  def test_xsd_media(self):
    """XSD_MEDIA should always return the correct MediaType object"""
    media = XSD_MEDIA()
    self.assertEqual(media.mime_type, "application/xml")
    self.assertEqual(media.file_extension, "xsd")
    
  def test_xls_media(self):
    """XLS_MEDIA should always return the correct MediaType object"""
    media = XLS_MEDIA()
    self.assertEqual(media.mime_type, "application/vnd.ms-excel")
    self.assertEqual(media.file_extension, "xls")
    
  def test_html_media(self):
    """HTML_MEDIA should always return the correct MediaType object"""
    media = HTML_MEDIA()
    self.assertEqual(media.mime_type, "text/html")
    self.assertEqual(media.file_extension, "html")
    
  def test_json_media(self):
    """JSON_MEDIA should always return the correct MediaType object"""
    media = JSON_MEDIA()
    self.assertEqual(media.mime_type, "text/json")
    self.assertEqual(media.file_extension, "json")
    
  def test_create_rule_attribs(self):
    """create_rule_attribs should generate RewriteRule attributes given a ContentModel or ModelVersion"""
    # Make RewriteRule attributes from the ContentModel
    output = create_rule_attribs(self.cm)
    self.assertEqual(output['register'], get_default_register())
    self.assertEqual(output['label'], self.cm.__unicode__())
    self.assertEqual(output['description'], "Redirection rule for %s" % self.cm.__unicode__())
    self.assertEqual(output['pattern'], self.cm.regex_pattern())
          
    # Make RewriteRule attributes from the ModelVersion
    output = create_rule_attribs(self.mv)
    self.assertEqual(output['register'], get_default_register())
    self.assertEqual(output['label'], self.mv.__unicode__())
    self.assertEqual(output['description'], "Redirection rule for %s" % self.mv.__unicode__())
    self.assertEqual(output['pattern'], self.mv.regex_pattern())
    
  def test_create_rewrite_rule_type(self):
    """create_rewrite_rule should return a new RewriteRule"""
    # Check that the proper class is returned
    self.assertIsInstance(create_rewrite_rule(self.cm, "ContentModel"), RewriteRule)
    self.assertIsInstance(create_rewrite_rule(self.mv, "ModelVersion"), RewriteRule)
    
  def test_create_rewrite_rule_foreignkey(self):
    """create_rewrite_rule should create a relationship between the instance passed in and the rule created"""
    self.assertEqual(create_rewrite_rule(self.cm, "ContentModel"), self.cm.rewrite_rule)
    self.assertEqual(create_rewrite_rule(self.mv, "ModelVersion"), self.mv.rewrite_rule)
      
  def test_create_rewrite_rule_attributes(self):
    """create_rewrite_rule should return a RewriteRule with appropriate attributes"""    
    cm_rule = create_rewrite_rule(self.cm, "ContentModel")
    mv_rule = create_rewrite_rule(self.mv, "ModelVersion")
    
    self.assertEqual(cm_rule.register, get_default_register())
    self.assertEqual(cm_rule.label, self.cm.__unicode__())
    self.assertEqual(cm_rule.description, "Redirection rule for %s" % self.cm.__unicode__())
    self.assertEqual(cm_rule.pattern, self.cm.regex_pattern())
    
    self.assertEqual(mv_rule.register, get_default_register())
    self.assertEqual(mv_rule.label, self.mv.__unicode__())
    self.assertEqual(mv_rule.description, "Redirection rule for %s" % self.mv.__unicode__())
    self.assertEqual(mv_rule.pattern, self.mv.regex_pattern())
    
  def test_create_rewrite_rule_mappings(self):
    """create_rewrite_rule should return a RewriteRule with appropriate mappings"""
    cm_rule = create_rewrite_rule(self.cm, "ContentModel")
    mv_rule = create_rewrite_rule(self.mv, "ModelVersion")
    
    mv_xls_mapping = mv_rule.acceptmapping_set.get(media_type=XLS_MEDIA())
    self.assertEqual(mv_xls_mapping.redirect_to, self.mv.absolute_xls_path())
    mv_xsd_mapping = mv_rule.acceptmapping_set.get(media_type=XSD_MEDIA())
    self.assertEqual(mv_xsd_mapping.redirect_to, self.mv.absolute_xsd_path())
    mv_html_mapping = mv_rule.acceptmapping_set.get(media_type=HTML_MEDIA())
    self.assertEqual(mv_html_mapping.redirect_to, self.mv.content_model.my_html())
    mv_json_mapping = mv_rule.acceptmapping_set.get(media_type=JSON_MEDIA())
    self.assertEqual(mv_json_mapping.redirect_to, self.mv.content_model.my_json())
    
    cm_xls_mapping = cm_rule.acceptmapping_set.get(media_type=XLS_MEDIA())
    self.assertEqual(cm_xls_mapping.redirect_to, self.cm.absolute_latest_xls_path())
    cm_xsd_mapping = cm_rule.acceptmapping_set.get(media_type=XSD_MEDIA())
    self.assertEqual(cm_xsd_mapping.redirect_to, self.cm.absolute_latest_xsd_path())
    cm_html_mapping = cm_rule.acceptmapping_set.get(media_type=HTML_MEDIA())
    self.assertEqual(cm_html_mapping.redirect_to, self.cm.my_html())
    cm_json_mapping = cm_rule.acceptmapping_set.get(media_type=JSON_MEDIA())
    self.assertEqual(cm_json_mapping.redirect_to, self.cm.my_json())
    
    
    
    
    
    
    
    