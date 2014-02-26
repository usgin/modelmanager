from modelmanager.models import ContentModel, ModelVersion
from django import forms
from django.http import HttpResponse
from django.shortcuts import render
import csv
import usginmodels


def get_feature_types():
    return ["ActiveFault","BaseMetals","CommonAnalytes","FreeGas","GasIsotopes","IsotopesDissolved","MajorDissolvedConstituents","MinorDissolvedConstituents","Nitrogen","WaterDissolvedGas","WaterIsotopes","WaterQuality","BaseMetals","CommonAnalytes","FreeGas","GasIsotopes","IsotopesDissolved","MajorDissolvedConstituents","MinorDissolvedConstituents","Nitrogen","SingleAnalyte","WaterDissolvedGas","WaterIsotopes","WaterQuality","BaseMetals","CommonAnalytes","FreeGas","GasIsotopes","IsotopesDissolved","MajorDissolvedConstituents","MinorDissolvedConstituents","Nitrogen","WaterDissolvedGas","WaterIsotopes","WaterQuality","BoreholeLithInterval","BoreholeTemperature","DirectUseSite","BoreholeLithIntercept","DrillStemTest","GeothermalArea","HeatFlow","HeatFlow","HeatPumpFacility","BoreholeTemperatureLASLog","PhysicalSample","GasAnalysis","LiquidAnalysis","PowerPlantFacility","RadiogenicHeatProduction","Isotopes","NobleGases","RareEarths","SingleAnalytes","StableIsotopes","TraceElements","USeries","Volatiles","WRMajorElements","Hypocenter","BoreholeTemperatureGeophysicalLog","ThermalConductivity","ThermalSpring","ThermalSpring","VolcanicVent","FluidProduction","Wellheader","WellLog","WellTest"]

class UploadFileForm(forms.Form):
    # Redefine the constructor for this form
    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)

        # Set the feature_type field's choices to the available WFS FeatureTypes
        # self.fields['feature_type'].choices = get_feature_types()
        self.fields['feature_type'] = forms.ChoiceField(choices= [(typename, typename) for typename in get_feature_types()])


    file  = forms.FileField(
        label='Select a CSV file which uses the content model specified above',
        help_text='The first row of data must be the field names.'
    )
    content_model = forms.ModelChoiceField(queryset=ContentModel.objects.all(),
        widget=forms.Select(attrs={'class':'span5'})
    )
    version = forms.ModelChoiceField(queryset=ModelVersion.objects.all(),
        widget=forms.Select(attrs={'class':'span5'})
    )
    feature_type = forms.ChoiceField(choices=[],
        widget=forms.Select(attrs={'class':'span5'})
    )


#--------------------------------------------------------------------------------------
# Here is the actual view function for /validate/cm
#--------------------------------------------------------------------------------------
def validate_cm_form(req):
    if req.method == 'POST':
        form = UploadFileForm(req.POST, req.FILES)
        if form.is_valid() or not form.is_valid():

            uploadFile = req.FILES['file']

            if uploadFile.name.endswith(".csv"):


                models = usginmodels.get_models()

                for m in models:
                    if m.title == form.cleaned_data["content_model"].title:
                        for v in m.versions:
                            if v.version == form.cleaned_data["version"].version:
                                uri = v.uri
                                break

                valid, messages, dataCorrected, long_fields, srs = usginmodels.validate_file(
                    uploadFile,
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

            else:
                valid = False
                messages = ["Only CSV files may be validated."]

            context = {
                "valid": valid,
                "errors": messages,
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