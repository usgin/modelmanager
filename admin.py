from django.contrib import admin
from models import ContentModel, ModelVersion

#--------------------------------------------------------------------------------------
# This class defines some customizations of the admin interface for ContentModels
#--------------------------------------------------------------------------------------
class ContentModelAdmin(admin.ModelAdmin):
    # The Media class defines some additional media to include with an Admin page
    #     Points to a JS and CSS file that together add a Dojo-based WYSIWYG editor
    class Media:
        js = [
            'https://ajax.googleapis.com/ajax/libs/dojo/1.6.0/dojo/dojo.xd.js',
            '/static/contentmodels/js/editor.js'
        ]
        css = {
            'all': [ '/static/contentmodels/css/editor.css']
        }        
        
    # Fields to display:
    list_display = ['__unicode__', 'latest_xsd_link', 'latest_xls_link', 'rewrite_rule_link']
    
    # Fields to exclude from the edit form
    exclude = ['rewrite_rule']
    
    # Fields on which to base the search:
    search_fields = ['title', 'label']
admin.site.register(ContentModel, ContentModelAdmin)

#--------------------------------------------------------------------------------------
# This class defines some customizations of the admin interface for ModelVersions    
#--------------------------------------------------------------------------------------
class ModelVersionAdmin(admin.ModelAdmin):
    # Fields to display in the table:
    list_display = ['__unicode__', 'xsd_link', 'xls_link', 'rewrite_rule_link']
    
    # Do not display a field to define a RewriteRule. This is done automatically.
    exclude = ['rewrite_rule']
    
    # Fields to use in filtering on the right-hand-side:
    list_filter = ['content_model']
    
    # How to order the ModelVersions:
    ordering = ['content_model__title', 'version']
    
    # Fields on which to base the search:
    search_fields = ['content_model__title']
admin.site.register(ModelVersion, ModelVersionAdmin)