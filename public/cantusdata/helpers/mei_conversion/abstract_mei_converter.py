import os
import signal
from abc import ABCMeta, abstractmethod
from multiprocessing import Pool

import pymei

DEFAULT_MIN_GRAM = 2
DEFAULT_MAX_GRAM = 10


class AbstractMEIConverter:
    __metaclass__ = ABCMeta

    TYPE = "cantusdata_music_notation"

    def __init__(self, file_name, siglum_slug, min_gram=DEFAULT_MIN_GRAM, max_gram=DEFAULT_MAX_GRAM):
        self.file_name = file_name
        self.siglum_slug = siglum_slug

        self.min_gram = min_gram
        self.max_gram = max_gram

        self.doc = pymei.documentFromFile(str(file_name), False).getMeiDocument()
        self.page_number = getPageNumber(file_name)

    @classmethod
    def convert(cls, directory, siglum_slug, processes=None, **options):
        mei_files = cls._get_file_list(directory)

        if processes == 0:
            def process_file(file_name):
                ngrams = cls._process_file(file_name, siglum_slug, **options)
                return file_name, ngrams

            ngram_generator = (process_file(file_name) for file_name in mei_files)
        else:
            args = ((cls, file_name, siglum_slug, options) for file_name in mei_files)
            pool = Pool(initializer=init_worker, processes=processes)
            ngram_generator = pool.imap(process_file_in_worker, args)

        for (file_name, ngrams) in ngram_generator:
            print 'Processed', file_name
            yield ngrams

    @classmethod
    def _get_file_list(cls, directory):
        """Generate a list of files to process"""
        mei_files = []

        for root, dirs, files in os.walk(directory):
            # Skip .git directories
            try:
                git_index = dirs.index('.git')
            except ValueError:
                pass
            else:
                del dirs[git_index]

            for f in files:
                if f.startswith("."):
                    continue

                if os.path.splitext(f)[1] == '.mei':
                    mei_files.append(os.path.join(root, f))

        mei_files.sort()
        return mei_files

    @classmethod
    def _process_file(cls, file_name, siglum_slug, **options):
        print 'Processing {}...'.format(file_name)

        inst = cls(file_name, siglum_slug, **options)
        return inst.process()

    @abstractmethod
    def process(self):
        raise NotImplementedError('process()')


def init_worker():
    # Allow KeyboardInterrupt to propagate to the parent process
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def process_file_in_worker(params):
    cls, file_name, siglum_slug, options = params

    ngrams = list(cls._process_file(file_name, siglum_slug, **options))

    return file_name, ngrams


def getPageNumber(ffile):
    """
    Extract the page number from the file name

    :param ffile:
    :return: page number as a string
    """
    return str(ffile).split('_')[-1].split('.')[0]
