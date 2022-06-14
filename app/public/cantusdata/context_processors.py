import os


def export_vars(request):
    data = {}
    data["APP_VERSION"] = os.environ["APP_VERSION"]
    return data
