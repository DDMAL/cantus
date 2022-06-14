import os
import signal
from abc import ABCMeta, abstractmethod
from multiprocessing import Pool
from django.conf import settings

import pymei
import solr

DEFAULT_MIN_GRAM = 2
DEFAULT_MAX_GRAM = 10


class AbstractMEIConverter(metaclass=ABCMeta):
    TYPE = "cantusdata_music_notation"

    def __init__(
        self,
        file_name,
        siglum_slug,
        manuscript_id,
        min_gram=DEFAULT_MIN_GRAM,
        max_gram=DEFAULT_MAX_GRAM,
    ):
        self.file_name = file_name
        self.siglum_slug = siglum_slug
        self.manuscript_id = manuscript_id

        self.min_gram = min_gram
        self.max_gram = max_gram

        self.doc = pymei.documentFromFile(
            str(file_name), False
        ).getMeiDocument()
        self.page_number = getPageNumber(file_name)

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        self.image_uri = getImageURI(file_name, manuscript_id, solrconn)

    @classmethod
    def convert(cls, directory, siglum_slug, id, processes=None, **options):
        mei_files = cls._get_file_list(directory)

        if processes == 0:
            processed = cls._process_in_sequence(
                mei_files, siglum_slug, id, **options
            )
        else:
            processed = cls._process_in_parallel(
                mei_files, siglum_slug, id, processes=processes, **options
            )

        return mei_files, processed

    @classmethod
    def _get_file_list(cls, directory):
        """Generate a list of files to process"""
        mei_files = []

        for root, dirs, files in os.walk(directory):
            # Skip .git directories
            try:
                git_index = dirs.index(".git")
            except ValueError:
                pass
            else:
                del dirs[git_index]

            for f in files:
                if f.startswith("."):
                    continue

                if os.path.splitext(f)[1] == ".mei":
                    mei_files.append(os.path.join(root, f))

        mei_files.sort()
        return mei_files

    @classmethod
    def _process_in_sequence(cls, mei_files, siglum_slug, id, **options):
        for file_name in mei_files:
            ngrams = cls.process_file(file_name, siglum_slug, id, **options)
            yield file_name, ngrams

    @classmethod
    def _process_in_parallel(
        cls, mei_files, siglum_slug, id, processes, **options
    ):
        pool = Pool(initializer=init_worker, processes=processes)
        args = (
            (cls, file_name, siglum_slug, id, options)
            for file_name in mei_files
        )

        return pool.imap(process_file_in_worker, args)

    @classmethod
    def process_file(cls, file_name, siglum_slug, id, **options):
        inst = cls(file_name, siglum_slug, id, **options)
        return inst.process()

    @abstractmethod
    def process(self):
        raise NotImplementedError("process()")


def init_worker():
    # Allow KeyboardInterrupt to propagate to the parent process
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def process_file_in_worker(params):
    cls, file_name, siglum_slug, id, options = params

    ngrams = list(cls.process_file(file_name, siglum_slug, id, **options))

    return file_name, ngrams


def getPageNumber(ffile):
    """
    Extract the page number from the file name

    :param ffile:
    :return: image URI as a string
    """
    return str(ffile).split("_")[-1].split(".")[0]


def getImageURI(ffile, manuscript_id, solrconn):
    """
    Extract the page number from the file name
    and get the corresponding image URI from Solr

    :param ffile:
    :param manuscript_id:
    :param solrconn:
    :return: image URI as a string
    """

    # Send the value of the folio name to Solr and get the corresponding URI
    folio_name = getPageNumber(ffile)
    composed_request = (
        'type:"cantusdata_folio" AND manuscript_id:{0} AND number:{1}'.format(
            manuscript_id, folio_name
        )
    )

    result = solrconn.query(composed_request, rows=1, fields=["image_uri"])
    return result.results[0]["image_uri"]
