from django.contrib import admin

from cantusdata.models.manuscript import Manuscript
from cantusdata.models.chant import Chant


class ManuscriptAdmin(admin.ModelAdmin):
    pass


class ChantAdmin(admin.ModelAdmin):
    pass

admin.site.register(Manuscript, ManuscriptAdmin)
admin.site.register(Chant, ChantAdmin)
