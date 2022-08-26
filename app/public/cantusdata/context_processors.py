import os
from cantusdata.settings import is_development


def export_vars(request):
    data = {}
    data["APP_VERSION"] = os.environ["APP_VERSION"]
    data["IS_DEVELOPMENT"] = is_development
    return data
