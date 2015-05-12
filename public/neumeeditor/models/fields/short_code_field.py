import re
from django.db import models


class ShortCodeField(models.CharField):
    unacceptable_chars = "[^a-z0-9\._]"
    duplicate_spaces_and_dots = "[\ .]+"
    description = "A short string representing a glyph name"

    def pre_save(self, model_instance, add):
        """
        We want to filter-out the undesirable characters.
        """
        # Turn spaces and dots into single dots
        new_code = re.sub(self.duplicate_spaces_and_dots, '.', model_instance.short_code.strip().lower())
        # Filter out everything bad
        model_instance.short_code = re.sub(self.unacceptable_chars, '', new_code)
        return model_instance.short_code
