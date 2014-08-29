from django.core.files.storage import FileSystemStorage
import os


class MediaFileSystemStorage(FileSystemStorage):
    """
    Code found at http://stackoverflow.com/questions/15885201/
    django-uploads-discard-uploaded-duplicates-use-existing-file-md5-based-check
    """

    def get_available_name(self, name):
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(MediaFileSystemStorage, self)._save(name, content)


def media_file_name(instance, filename):
    h = instance.md5sum
    basename, ext = os.path.splitext(filename)
    return os.path.join('mediafiles', h[0:1], h[1:2], h + ext.lower())
