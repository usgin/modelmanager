import urllib2
from lxml import etree

class WfsBase():  
  url = None              # The URL of the WFS GetCapabilities document, passed into class constructor
  url_is_valid = True     # Whether or not the URL points to a valid WFS GetCapabilities document
  errors = []             # Any errors encountered during fetching and parsing of the given URL
  doc = None              # The document returned from the given URL
  parsed_doc = None       # The document parsed by lxml and represented as an ElementTree
    
  # Function to perform an HTTP request to get the document at the given URL
  def fetch_document(self):
    # Just return the document if it has already been fetched
    if self.doc is not None: return self.doc
    
    # Open the URL and return the response
    try:
      self.doc = urllib2.urlopen(self.url)
      return self.doc
    
    # There was an error processing the URL
    except urllib2.URLError, err:
      self.errors.append({"urlError": err})
    
    # There was an HTTP error retrieving the document  
    except urllib2.HTTPError, err:
      self.errors.append({"httpError": err})
    
    # Some error was encountered, set the invalid flag and return nothing
    self.url_is_valid = False
    return None
    
  # Function to parse the returned document into an ElementTree
  def fetch_parsed_doc(self):
    # Just return the ElementTree if it has already been parsed
    if self.parsed_doc is not None: return self.parsed_doc
    
    # Fetch the document
    doc = self.fetch_document()

    # Parse the document using lxml.etree and return the ElementTree
    try:
      self.parsed_doc = etree.parse(doc)
      return self.parsed_doc
    
    # There was an error while parsing the document
    except etree.ParseError, err:
      self.errors.append({"parseError": err})
    
    # Some error was encountered, set the invalid flag and return nothing  
    self.url_is_valid = False
    return None    