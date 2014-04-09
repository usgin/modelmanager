from modelmanager.models import ContentModel, ModelVersion
from django import forms
from django.http import HttpResponse
from django.shortcuts import render
import csv
import usginmodels
import io


# def get_feature_types():
#     return ['ActiveFault','SingleAnalyte','BaseMetals','WaterIsotopes','MajorDissolvedConstituents','FreeGas','WaterDissolvedGas','WaterQuality','IsotopesDissolved','GasIsotopes','Nitrogen','CommonAnalytes','MinorDissolvedConstituents','BoreholeLithIntercept','BoreholeLithInterval','BoreholeTemperature','ContourLine','DirectUseSite','DrillStemTest','Fault','ShearDisplacementStructureView','GeologicUnitView','ContactView','FluidFluxInjection','GeologicReservoir','GeothermalArea','GeothermalFluidProduction','PowerPlantFacility','GravityStation','HeatFlow','HeatPumpFacility','HydraulicProperty','PhysicalSample','LiquidAnalysis','GasAnalysis','PlantProduction','RadiogenicHeatProduction','Isotopes','NobleGases','RareEarths','Volatiles','StableIsotopes','USeries','WRMajorElements','SingleAnalytes','TraceElements','EarthquakeHypocenter','Hypocenter','MDThermalConductivity','ThermalConductivity','ThermalSpring','VolcanicVent','FluidProduction','Wellheader','WellLog','WellTest']


#--------------------------------------------------------------------------------------------------------
# A Form to gather user's input required to validate a CSV against some feature type in a ModelVersion
#--------------------------------------------------------------------------------------------------------
class UploadFileForm(forms.Form):
    # Redefine the constructor for this form
    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)

        # Get a list of the all the layer names
        layernames = []
        models = usginmodels.get_models()
        for model in models:
            for version in model.versions:
                for layer in version.layers:
                    if layer.layer_name not in layernames:
                        layernames.append(layer.layer_name)
        layernames = sorted(layernames)

        # layernames = get_feature_types()
        self.fields['feature_type'] = forms.ChoiceField(choices= [(typename, typename) for typename in layernames],             widget=forms.Select(attrs={'class':'span5'})
        )

    file  = forms.FileField()

    content_model = forms.ModelChoiceField(queryset=ContentModel.objects.all(),
        widget=forms.Select(attrs={'class':'span5'})
    )
    version = forms.ModelChoiceField(queryset=ModelVersion.objects.all(),
        widget=forms.Select(attrs={'class':'span5'})
    )
    # feature_type = forms.ChoiceField()


#--------------------------------------------------------------------------------------
# Here is the actual view function for /validate/cm
#--------------------------------------------------------------------------------------
def validate_cm_form(req):
    if req.method == 'POST':
        form = UploadFileForm(req.POST, req.FILES)
        if form.is_valid():

            uploadFile = req.FILES['file']


            if uploadFile.name.endswith(".csv"):

                try:
                    fileCSV = io.StringIO(unicode(uploadFile.read()), newline=None)

                except:
                    valid = False
                    messages = "Unable to read the CSV file. Check the file for invalid characters."
                    datastr = None

                else:
                    models = usginmodels.get_models()

                    for m in models:
                        if m.title == form.cleaned_data["content_model"].title:
                            for v in m.versions:
                                if v.version == form.cleaned_data["version"].version:
                                    uri = v.uri
                                    break

                    try:
                        valid, messages, dataCorrected, long_fields, srs = usginmodels.validate_file(
                            fileCSV,
                            uri,
                            form.cleaned_data["feature_type"]
                        )

                        # Original Working
                        # csvstr = ""
                        # for line in uploadFile:
                        #     csvstr += str(line)

                        datastr = ""
                        for line in dataCorrected:
                            for ele in line:
                                datastr += "\"" + str(ele) + "\","
                            datastr += "\r\n"

                    except:
                        valid = False
                        messages = "Invalid Layer"
                        datastr = None

            else:
                valid = False
                messages = "Only CSV files may be validated."
                datastr = None

            context = {
                "valid": valid,
                "messages": messages,
                "dataCorrected": datastr,
                "filepath": uploadFile.name
            }
            # Render the results as HTML
            return render(req, 'validation/cm-results-bootstrap.html', context)
    else:
        form = UploadFileForm()
    return render(req, 'validation/cm-form-bootstrap.html', { 'form': form })


def download_csv(req):

    dataCorrected = req.POST['new_data']

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="CorrectedData.csv"'

    # This is really dumb
    dataCorrected = str(dataCorrected).splitlines()
    usgincsvreader = csv.reader(dataCorrected, delimiter=',', quotechar='"')
    usgincsvwriter = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    usgincsvwriter.writerows(usgincsvreader)

    response.close()

    return response