

def strip_leading_characters(unstripped_string, lead):
    """
    Strip the lead from a string.

    :param unstripped_string: The string to strip.  Ex: "excommunicate"
    :param lead: The lead to remove.  Ex: "ex"
    :return: The stripped string.  Ex: "communicate"
    """
    if unstripped_string.startswith(str(lead)):
        return unstripped_string[len(lead):]
    else:
        return unstripped_string

def strip_trailing_characters(unstripped_string, tail):
    """
    Strip the tail from a string.

    :param unstripped_string: The string to strip.  Ex: "leading"
    :param tail: The trail to remove.  Ex: "ing"
    :return: The stripped string.  Ex: "lead"
    """
    if unstripped_string.endswith(str(tail)):
        return unstripped_string[:len(tail)]
    else:
        return unstripped_string
