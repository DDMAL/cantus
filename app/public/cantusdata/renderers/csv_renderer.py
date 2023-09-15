from typing import List
from rest_framework.renderers import BaseRenderer


class CSVRenderer(BaseRenderer):
    """
    Provides a renderer class which serializes a response to CSV.
    The renderer assumes that the response data is a list of dictionaries
    with a consistent set of keys (which become the header row in the csv
    result).
    """

    media_type = "text/csv"
    format = "csv"

    def render(self, data, media_type=None, renderer_context=None):
        headers: str = ",".join([str(key) for key in data[0].keys()])
        rows: List[str] = [",".join([str(val) for val in row.values()]) for row in data]
        csv_str: str = "\n".join([headers] + rows)
        return bytes(csv_str, encoding="utf-8")
