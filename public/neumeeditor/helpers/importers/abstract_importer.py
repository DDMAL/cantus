

class AbstractImporter():
    """
    Abstract class describing a file importer
    """
    def __init__(self, file_string, file_name=None):
        self.file_string = file_string
        self.file_name = file_name

    def import_data(self):
        raise NotImplementedError("AbstractImporter is abstract.")
