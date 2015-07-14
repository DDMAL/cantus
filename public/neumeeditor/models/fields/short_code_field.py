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
    new_code = replace_common_words(re.sub(unacceptable_chars, '', new_code))
    # Duplicates once more
    return re.sub(duplicate_spaces_and_dots, '.', new_code)

def replace_common_words(input):
    # Neumes that we will shorten
    replacements = [
        ("torculus", "torc"),
        ("tractulus", "trac"),
        ("punctum", "pun"),
        ("stropha", "stro"),
        ("virga", "vir"),
        ("porrectus", "por"),
        ("ancus", "anc"),
        ("status", "stra"),
        ("quadratus", "q"),
        ("quassus", "quas"),
        ("oriscus", "ori"),
        ("episema", "e"),
        ("clivis", "cli"),
        ("rotundus", "r"),
        ("liquescent", "l"),
        ("quilismapes", "pes.quil"),
        ("two", "2"),
        ("three", "3"),
        # Important to strip simple
        (".simple", ""),
        # Some other language stuff
        ("langer", "long"),
        (".zweiter", ""),
        (".abstrich", "")
    ]
    return replace_words(input, replacements)

def replace_words(input, replacements):
    for replacement in replacements:
        old, new = replacement
        input = re.sub(old, new, input)
    return input
