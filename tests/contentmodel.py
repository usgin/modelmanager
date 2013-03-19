from django.test import TestCase
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile
from django.core.files import File
from django.conf import settings
import datetime, os, shutil
from modelmanager.models import ContentModel, ModelVersion, add_target_to_anchors

class ContentModelTestCase(TestCase):
    fixtures = [
            "tests/cm-example.json"
        ]
        
    def setUp(self):
        self.example = ContentModel.objects.get(label="example")
    
    def tearDown(self):
        # Remove any files that may have been added in the course of adding versions
        example_path = os.path.join(settings.MEDIA_ROOT, self.example.folder_path())
        if os.path.exists(example_path):
            shutil.rmtree(example_path)
    
    def createTwoVersions(self):
        """Create two version, return the newer of the two"""
        # Create dummy files to be the XSD and XLS files
        dummy_xsd_content = ContentFile("Dummy Schema File")
        dummy_xls_content = ContentFile("Dummy Excel File")
        dummy_xsd_file = File(dummy_xsd_content, "dummyFile.xsd")
        dummy_xls_file = File(dummy_xls_content, "dummyFile.xls")
        
        # Create an older version
        v2 = ModelVersion.objects.create(
                content_model = self.example,
                version = "1.0",
                #date_created = datetime.datetime.now() - datetime.timedelta(days=3),
                xsd_file = dummy_xsd_file,
                xls_file = dummy_xls_file
            )
        
        # Create a version right now
        v1 = ModelVersion.objects.create(
                content_model = self.example,
                version = "2.0",
                #date_created = datetime.datetime.now(),
                xsd_file = dummy_xsd_file,
                xls_file = dummy_xsd_file
            )
            
        # Return the newer version
        return {'new': v1, 'old': v2}

    def stripped_regex(self):
        return "dataschema/%s/" % self.example.label

    def test_name(self):
        """The model's name should be equal to its title"""
        self.assertEqual(self.example.__unicode__(), self.example.title)
        
    def test_folder_path(self):
        """The model's folder path should be a slugified version of the title"""
        self.assertEqual(self.example.folder_path(), slugify(self.example.title))
        
    def test_latest_version_for_null(self):
        """When there are no versions of a model, the model's latest_version should return None"""
        self.assertIsNone(self.example.latest_version())
    
    def test_latest_version(self):
        """The model's latest_version should return the correct version"""
        v = self.createTwoVersions()['new']     
        self.assertEqual(self.example.latest_version(), v)
                
    def test_latest_version_number_for_null(self):
        """When there are no versions of a model, the model's latest_version_number should return None"""
        self.assertIsNone(self.example.latest_version_number())
            
    def test_latest_version_number(self):
        """The model's latest_version_number should return the correct number"""
        v = self.createTwoVersions()['new']
        self.assertEqual(self.example.latest_version_number(), v.version)
        
    def test_date_updated_for_null(self):
        """When there are no versions the model's update date should be None"""
        self.assertIsNone(self.example.date_updated())
        
    def test_date_updated(self):
        """The model's date_updated should match the creation date of the latest version"""
        v = self.createTwoVersions()['new']
        self.assertEqual(self.example.date_updated(), v.date_created)
        
    def test_iso_date_updated_for_null(self):
        """When there are no versions the model's iso_date_updated should be None"""
        self.assertIsNone(self.example.iso_date_updated())
        
    def test_iso_date_updated(self):
        """The model's iso_date_updated should be an ISO representation of the latest version's creation date"""
        v = self.createTwoVersions()['new']
        self.assertEqual(self.example.iso_date_updated(), v.date_created.isoformat())
        
    def test_discussion_for_drupal(self):
        """The model's discussion_for_drupal function should return discussion text where all <a> tags have target='_blank'"""
        expected = "The discussion of the content model <a href='http://google.com/' target='_blank'>Fake Anchor</a>"
        self.assertEqual(self.example.discussion_for_drupal(), expected)
        
    def test_status_for_drupal(self):
        """The model's status_for_drupal function should return status text where all <a> tags have target='_blank'"""
        expected = "The status of the content model <a href='http://google.com/' target='_blank'>Fake Anchor</a>"
        self.assertEqual(self.example.status_for_drupal(), expected)
    
    def test_description_for_drupal(self):
        """The model's description_for_drupal function should return status text where all <a> tags have target='_blank'"""
        expected = "The description of the content model <a href='http://google.com/' target='_blank'>Fake Anchor</a>"
        self.assertEqual(self.example.description_for_drupal(), expected)
    
    def test_add_target_to_anchors(self):
        """Utility function should add target attributes to any arbitrary string's <a> tags"""        
        self.assertEqual(add_target_to_anchors("no anchors"), "no anchors")
        self.assertEqual(add_target_to_anchors("something <a href='whatever'>hello</a>"), "something <a href='whatever' target='_blank'>hello</a>")
        self.assertEqual(add_target_to_anchors("something <a href='whatever'>hello</a> another <a href='http://google.com'>Google</a>"), "something <a href='whatever' target='_blank'>hello</a> another <a href='http://google.com' target='_blank'>Google</a>")
        self.assertEqual(add_target_to_anchors("something <a href='whatever' target='_self'>hello</a>"), "something <a href='whatever' target='_blank'>hello</a>")
        self.assertEqual(add_target_to_anchors('something <a href="whatever" target="_self">hello</a>'), 'something <a href="whatever" target=\'_blank\'>hello</a>')
    
    def test_recent_versions(self):
        """The model's recent_versions method should return the most recent three versions, from current to 2nd oldest"""
        v = self.createTwoVersions()
        output = self.example.recent_versions()
        self.assertEqual(output[0].version, v["new"].version)
        self.assertEqual(output[1].version, v["old"].version)        
    
    def test_my_pretty_html(self):
        """The model's my_pretty_html method should return the complete URL for the model's bootstrap page"""
        self.assertEqual(self.example.my_pretty_html(), "%s/models/#%s" % (settings.BASE_URL.rstrip("/"), self.example.label))
                
    #Created by Genhan
    def test_absolute_latest_xsd_path_for_null(self):
        """When there are no versions the absolute path to the latest version's XSD file is none"""
        self.assertIsNone(self.example.absolute_latest_xsd_path())
 
    def test_absolute_latest_xsd_path(self):
        """The xsd file should be for the latest version"""
        v = self.createTwoVersions()['new']
        v_abs_path = '%s/%s' % (settings.BASE_URL.rstrip('/'), v.xsd_file.url.lstrip('/'))
        self.assertEqual(self.example.absolute_latest_xsd_path(), v_abs_path)
        
    def test_absolute_latest_xls_path_for_null(self):
        """When there are no versions the absolute path to the latest version's XLS file is none"""
        self.assertIsNone(self.example.absolute_latest_xls_path())
    
    def test_absolute_latest_xls_path(self):
        """The xls file should be for the latest version"""
        v = self.createTwoVersions()['new']
        v_abs_path = '%s/%s' % (settings.BASE_URL.rstrip('/'), v.xls_file.url.lstrip('/'))
        self.assertEqual(self.example.absolute_latest_xls_path(), v_abs_path)
        
    def test_latest_xsd_link_for_null(self):
        """When there are no versions the link to the latest version's XSD file is none"""
        self.assertIsNone(self.example.latest_xsd_link())
    
    def test_latest_xsd_link(self):
        """There should be a link element for the latest version's xsd file"""
        v = self.createTwoVersions()['new']
        v_link = '<a href="%s/%s">%s</a>' % (settings.BASE_URL.rstrip('/'), v.xsd_file.url.lstrip('/'), v.xsd_file.name.split('/')[-1])
        self.assertEqual(self.example.latest_xsd_link(), v_link)
        
    def test_latest_xls_link_for_null(self):
        """When there are no versions the link to the latest version's XSD file is none"""
        self.assertIsNone(self.example.latest_xls_link())
    
    def test_latest_xls_link(self):
        """There should be a link element for the latest version's xls file"""
        v = self.createTwoVersions()['new']
        v_link = '<a href="%s/%s">%s</a>' % (settings.BASE_URL.rstrip('/'), v.xls_file.url.lstrip('/'), v.xls_file.name.split('/')[-1])
        self.assertEqual(self.example.latest_xls_link(), v_link)
    
    def test_my_html(self):
        """The my_html should return the correct url to the model's html page"""
        url = '%s/contentmodel/%s.html' % (settings.BASE_URL.rstrip('/'), self.example.pk)
        self.assertEqual(self.example.my_html(), url)
        
    def test_my_json(self):
        """The my_json should return the correct url to the model's json page"""
        url = '%s/contentmodel/%s.json' % (settings.BASE_URL.rstrip('/'), self.example.pk)
        self.assertEqual(self.example.my_json(), url)
    
    def test_my_atom(self):
        """The my_atom should return the correct url to the model's atom page"""
        url = '%s/contentmodel/%s.xml' % (settings.BASE_URL.rstrip('/'), self.example.pk)
        self.assertEqual(self.example.my_atom(), url)
        
    def test_stripped_regex(self):
        """The stripped_regex should return the label's path """
        self.assertEqual(self.example.stripped_regex(), self.stripped_regex())
        
    def test_regex_pattern(self):
        """The stripped_regex should generate the regular expression pattern for the label's path"""
        regex = '^%s(\.[a-zA-Z]{3,4}|/)?$' % self.stripped_regex()
        self.assertEqual(self.example.regex_pattern(), regex)

    def test_relative_uri(self):
        """The relative_uri should generate the relative uri for the ContentModel"""
        uri = '/uri-gin/%s/%s' % (settings.URI_REGISTER_LABEL, self.stripped_regex())
        self.assertEqual(self.example.relative_uri(), uri)
        
    def test_absolute_uri(self):
        """The absolute_uri should generate the absolute uri for the ContentModel"""
        uri = '%s/uri-gin/%s/%s' % (settings.BASE_URL.rstrip('/'), settings.URI_REGISTER_LABEL, self.stripped_regex())
        self.assertEqual(self.example.absolute_uri(), uri)
        
    def test_rewrite_rule_link(self):
        """The rewrite_rule_link should return a link to this ContentModel's RewriteRule"""
        url = '<a href="/admin/uriredirect/rewriterule/%s">Edit Rule</a>' % self.example.rewrite_rule.pk
        self.assertEqual(self.example.rewrite_rule_link(), url)

    def test_serialized(self):
        """The serialized should return a json object"""
        vs = self.createTwoVersions()
        expect_json = {
            'title': self.example.title,
            'uri': self.example.absolute_uri(),
            'description': self.example.description,
            'discussion': self.example.discussion,
            'status': self.example.status,
            'date_updated': self.example.iso_date_updated(),
            'versions': [ mv.serialized() for mv in self.example.modelversion_set.all() ]
        }        
        self.assertEqual(self.example.serialized(), expect_json)