import re

def alpha_numeric(text):
    """
    Returns the text with everything except alphanumeric characters stripped
    """
    return re.sub(r'\W+', '', text)