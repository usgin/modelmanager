from WfsBase import WfsBase

#--------------------------------------------------------------------------------------
# A class representing a WFS GetFeature document.
#   Constructor requires a WfsCapabilities object, the requested TypeName and MaxFeatures
#   Inherits from WfsBase, which performs HTTP requests and XML parsing
#--------------------------------------------------------------------------------------
class WfsGetFeature(WfsBase):
  def __init__(self, capabilities, feature_type, number_of_features):
    # WfsCapabilites object constructs the GetFeature URL
    self.url = capabilities.get_feature_url(feature_type, number_of_features)
    self.feature_type = feature_type
  
  #--------------------------------------------------------------------------------------
  # Function to setup for schema validation by finding the appropriate elements and
  #   passing them to the ValidationResults class to actually perform validation
  #--------------------------------------------------------------------------------------  
  def validate(self, modelversion):
    # Retrieve the GetFeature document, parsed by lxml
    parsed_doc = self.fetch_parsed_doc()
    
    # Grab the namespace map
    ns = parsed_doc.getroot().nsmap
    
    # Gather elements of the requested FeatureType
    elements = parsed_doc.xpath("//%s" % self.feature_type, namespaces=ns)
    
    # Retrieve the XMLSchema object responsible for validating this ModelVersion's schema
    schema = modelversion.schema_validator()
    
    # Perform validation on each element
    return ValidationResults(elements, schema)
    
  def get_namespaces(self):
    # Retrieve the GetFeature document, parsed by lxml
    parsed_doc = self.fetch_parsed_doc()
    
    
  
#--------------------------------------------------------------------------------------
# Class to perform schema validation for each element in a wfs:FeatureCollection
#--------------------------------------------------------------------------------------
class ValidationResults():
  results = []
  errors = []
  valid = True
  
  # Constructor function requires a set of elements to validate and a schema
  #   to validate them against.
  def __init__(self, elements, schema):
    # Provide a count for the total number of elements validated
    self.number_of_elements = len(elements)
    
    # If no elements were passed in, the result is not valid
    if self.number_of_elements == 0:
      self.valid = False
      
      # A little class to mimic the error objects that lxml would spit out
      class Error(object):
        def __init__(self, message):
          self.message = message
      
      # Append an error to the array and drop out of the function    
      self.errors.append(Error("No elements were validated."))
      return
    
    # Otherwise, loop through elements
    for element in elements:
      # Validate each element
      valid = schema.validate(element)
      
      # Mark the entire result invalid if any one element fails
      if not valid: self.valid = False
      
      # Append the element and whether or not it validated to the results set
      self.results.append({
          "valid": valid,
          "element": element                   
        })
        
      # Grab the error log from the etree.XMLSchema object
      self.errors = schema.error_log
      
      # De-duplicate the error log
      self.deduplicate_errors()
      
  # Function to count the number of valid elements
  def valid_count(self):
    return len([ result for result in self.results if result['valid'] ])
  
  # Function to count the number of invalid elements
  def invalid_count(self):
    return len([ result for result in self.results if not result['valid'] ])
    
  # Function to remove duplicate errors from the log
  def deduplicate_errors(self):
    self.errors = list(set(self.errors))
      
    
    