from WfsBase import WfsBase

#--------------------------------------------------------------------------------------
# A class representing a WFS GetCapabilities document.
#     Constructor requires a URL for the GetCapabilities document
#     Inherits from WfsBase, which performs HTTP requests and XML parsing
#--------------------------------------------------------------------------------------
class WfsCapabilities(WfsBase):
    version = None                    # The WFS version, parsed from the GetCapabilites document
    feature_types = []            # The names of FeatureTypes available from the WFS
    
    # Constructor function. Requires a URL passed in as a string
    def __init__(self, url):
        # Set the object's URL value
        self.url = url
        
        # Get a list of FeatureTypes. Any errors encountered in the process will be logged to self.errors
        self.set_feature_types()
            
    # Function to set FeatureType list according to the document at the given URL
    def set_feature_types(self):
        # Fetch the parsed document
        parsed_doc = self.fetch_parsed_doc()
        
        # Determine the WFS version, drop lxml's "smart string" in this case
        self.version = parsed_doc.xpath('@version', smart_strings=False)
        if len(self.version) > 0: self.version = self.version[0]
        
        # Namespaces are different depending on the version
        if self.version is '1.0.0' or '1.1.0':
            ns = { 'wfs': 'http://www.opengis.net/wfs' }
        elif self.version is '2.0.0':
            ns = { 'wfs': 'http://www.opengis.net/wfs/2.0' }
        else:
            # There was some issue with getting the WFS version
            self.errors.append({"capabilitiesError": "Could not determine WFS version"})
            self.url_is_valid = False
            return
        
        # Get the FeatureType Names via XPath, plug them into self.feature_types
        feature_type_elements = parsed_doc.xpath('//wfs:FeatureTypeList/wfs:FeatureType/wfs:Name', namespaces=ns)
        self.feature_types = [ ftype.text for ftype in feature_type_elements ]
        
    # Function to spell out a GetFeature URL given the name of a FeatureType and the number of features
    def get_feature_url(self, feature_type_name, number_of_features):
        # Return nothing if the URL is invalid
        if not self.url_is_valid: return None
        
        # Fetch the parsed_doc
        parsed_doc = self.fetch_parsed_doc()
        
        # Make sure that the FeatureType requested is one of the available FeatureTypes
        if feature_type_name not in self.feature_types: return None 
        
        # Namespace setup for later XPath expressions
        ns = { 
                'wfs': 'http://www.opengis.net/wfs', 
                'ows': 'http://www.opengis.net/ows',
                'xlink': 'http://www.w3.org/1999/xlink'
            }
        
        # Read URLs for GetFeature operations from the GetCapabilities document
        if self.version == '1.0.0':
            base_url = parsed_doc.xpath(
                    '//wfs:Capability/wfs:Request/wfs:GetFeature/wfs:DCPType/wfs:HTTP/wfs:Get/@onlineResource',
                    namespaces=ns
                )
        elif self.version in ['1.1.0', '2.0.0']:
            base_url = parsed_doc.xpath(
                    '//ows:OperationsMetadata/ows:Operation[@name="GetFeature"]/ows:DCP/ows:HTTP/ows:Get/@xlink:href',
                    namespaces=ns
                )
        else:
            # There was some issue locating the GetFeature operation's description
            self.errors.append({"capabilitiesError": "Could not determine the GetFeature URL"})
            self.url_is_valid = False
            return None

            
        # Pull the base_url from the list returned by the xpath() method
        if len(base_url) > 0: base_url = base_url[0]

        # Make sure there's a ? after the base_url
        base_url = "%s?" % base_url.rstrip("?")

        # Build the GetFeature URL
        param_values = (base_url, self.version, feature_type_name)
        url = "%s&service=WFS&version=%s&request=GetFeature&typename=%s" % param_values
        if number_of_features == 99:
            return url
        else:
            return "%s&maxfeatures=%s" % (url, number_of_features)
    