from django.core.files.base import ContentFile
from django.core.files import File

def create_dummy_files():
  # Create dummy files to be the XSD and XLS files
  dummy_xsd_content = ContentFile("Dummy Schema File")
  dummy_xls_content = ContentFile("Dummy Excel File")
  dummy_xsd_file = File(dummy_xsd_content, "dummyFile.xsd")
  dummy_xls_file = File(dummy_xls_content, "dummyFile.xls")
  
  return dummy_xsd_file, dummy_xls_file