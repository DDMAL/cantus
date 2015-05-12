import re
from django.db import models

unacceptable_chars = "[^a-z0-9\._]"
duplicate_spaces_and_dots = "[\ .]+"


class ShortCodeField(models.CharField):
    description = "A short string representing a glyph name"

    def pre_save(self, model_instance, add):
        model_instance.short_code = sanitize_short_code(model_instance.short_code)
        return model_instance.short_code


def sanitize_short_code(input):
    """
    We want to filter-out the undesirable characters.
    """
    # Turn spaces and dots into single dots
    new_code = re.sub(duplicate_spaces_and_dots, '.', input.strip().lower())
    # Filter out everything bad
    return re.sub(unacceptable_chars, '', new_code)
