import re
from django.db import models


class ShortCodeField(models.CharField):
    unacceptable_chars = "[^a-z0-9\._]"
    description = "A short string representing a glyph name"

    def pre_save(self, model_instance, add):
        """
        We want to filter-out the undesirable characters.
        """
        model_instance.short_code = re.sub(self.unacceptable_chars, '', model_instance.short_code.lower())
        return model_instance.short_code
