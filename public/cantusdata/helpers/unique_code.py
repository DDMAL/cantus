import re

def alpha_numeric_lower(text):
    """
    Returns the text with everything except alphanumeric characters stripped
    """
    return re.sub(r'\W+', '', text).lower()