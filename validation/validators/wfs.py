from modelmanager.models import ContentModel, ModelVersion
from WfsCapabilities import WfsCapabilities
from WfsGetFeature import WfsGetFeature
from django import forms
from django.http import HttpResponseNotAllowed
from django.shortcuts import render

#--------------------------------------------------------------------------------------
# A Form to gather user's input: Just the WFS URL
#     Also validates that the URL returns a GetCapabilities doc and that the WFS
#     provides some FeatureTypes
#--------------------------------------------------------------------------------------
class WfsSelectionForm(forms.Form):
    wfs_get_capabilities_url = forms.URLField(
        widget=forms.TextInput(attrs={'class':'span10', 'placeholder':'Enter a WFS GetCapabilities URL'})
    ) # Just one field in this form: the WFS GetCapabilities URL
    
    # Function to validate the wfs_get_capabilites_url
    def clean_wfs_get_capabilities_url(self):
        # Get the URL that the user provided
        url = self.cleaned_data['wfs_get_capabilities_url']
        
        # Check the validity of the given URL
        capabilities = WfsCapabilities(url)
        if not capabilities.url_is_valid:
            raise forms.ValidationError('The URL given is invalid')
            
        # Check that the WFS provides some FeatureTypes
        if len(capabilities.feature_types) is 0:
            raise forms.ValidationError('The WFS you specified does not provide any FeatureTypes')
        
#--------------------------------------------------------------------------------------
# A Form to gather user's input required to validate a WFS against some ModelVersion
#     Note that the constructor for the form requires a URL
#--------------------------------------------------------------------------------------
class WfsValidationParametersForm(forms.Form):
    # Redefine the constructor for this form to accomodate an input URL
    def __init__(self, url, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        
        # Set the feature_type field's choices to the available WFS FeatureTypes
        self.capabilities = WfsCapabilities(url)
        self.fields['feature_type'].choices = [ (typename, typename) for typename in self.capabilities.feature_types ]
        
        # Set the initial URL
        self.fields['url'].initial = url
        
    # Define form fields
    url = forms.URLField(widget=forms.HiddenInput) 
    content_model = forms.ModelChoiceField(queryset=ContentModel.objects.all(),
        widget=forms.Select(attrs={'class':'span4'})
    )
    version = forms.ModelChoiceField(queryset=ModelVersion.objects.all(),
        widget=forms.Select(attrs={'class':'span4'})
    )
    feature_type = forms.ChoiceField(choices=[],
        widget=forms.Select(attrs={'class':'span4'})
    )
    number_of_features = forms.IntegerField(
        widget=forms.Select(
            attrs={'class':'span1'},
            choices=((1,1), (10,10), (50, 50))
        )
    )

#--------------------------------------------------------------------------------------
# Here is the actual view function for /validate/wfs
#--------------------------------------------------------------------------------------
def validate_wfs_form(req):
    # Insure that HTTP requests are of the proper type
    allowed = [ 'GET', 'POST' ] 
    if req.method not in allowed:
        return HttpResponseNotAllowed(allowed)
    
    # When a data is passed in during a POST request...
    if req.method == 'POST':
        # ... determine if the req.POST contains WfsSelectionForm or WfsValidationParametersForm
        
        # This is a WfsValidationParametersForm
        if 'version' in req.POST:
            form = WfsValidationParametersForm(req.POST['url'], req.POST)
            
            # Check the form's validity
            if form.is_valid():
                # Perform WFS Validation
                feature_type = form.cleaned_data['feature_type']
                number_of_features = form.cleaned_data['number_of_features']
                modelversion = form.cleaned_data['version']
                get_feature_validator = WfsGetFeature(form.capabilities, feature_type, number_of_features)
                result = get_feature_validator.validate(modelversion)
                
                # Setup hash table for results rendering
                context = {
                        "valid": result.valid,
                        "valid_elements": result.valid_count(),
                        "url": get_feature_validator.url,
                        "errors": result.errors,
                        "modelversion": modelversion,
                        "feature_type": feature_type,
                        "number_of_features": number_of_features,
                        "wfs_base_url": get_feature_validator.url.split('?')[0]
                    }
                
                # Render the results as HTML
                return render(req, 'validation/wfs-results-bootstrap.html', context)
            
        # Otherwise it is treated as a WfsSelectionForm
        else:
            form = WfsSelectionForm(req.POST)
            
            # Check the form's validity
            if form.is_valid():
                # We need to send back a WfsValidationParametersForm, which takes a URL as input
                url = form.data['wfs_get_capabilities_url']
                second_form = WfsValidationParametersForm(url)
                return render(req, 'validation/wfs-form-bootstrap.html', { 'form': second_form, 'url': url })
                
    # A GET request should just a data-free WfsSelectionForm
    else:
        form = WfsSelectionForm()
        
    # You'll get here if it was a GET request, or if form validation failed
    return render(req, 'validation/wfs-form-bootstrap.html', { 'form': form })