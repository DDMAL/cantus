from django.contrib import admin
from neumeeditor.models.neume import Neume
from neumeeditor.models.neume_style import NeumeStyle


class NeumeAdmin(admin.ModelAdmin):
    pass


class NeumeStyleAdmin(admin.ModelAdmin):
    pass


admin.site.register(Neume, NeumeAdmin)
admin.site.register(NeumeStyle, NeumeStyleAdmin)
