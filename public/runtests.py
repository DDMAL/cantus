#!/usr/bin/env python
"""
Wrapper around Django's test runner to override global settings.

This is a pattern described (recommended?) at

    https://docs.djangoproject.com/en/1.9/topics/testing/advanced/#using-the-django-test-runner-to-test-reusable-applications
"""

import os
import sys
import contextlib
import argparse

import requests

import django
from django.conf import settings
from django.test.utils import get_runner
from cantusdata import settings as base_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tests', nargs='*', default=['cantusdata', 'neumeeditor'])
    args = parser.parse_args()

    failures = run_tests(args.tests)
    sys.exit(bool(failures))


def run_tests(tests):
    with create_test_solr_core():
        os.environ['DJANGO_SETTINGS_MODULE'] = 'cantusdata.test.test_settings'
        django.setup()
        TestRunner = get_runner(settings)
        test_runner = TestRunner()
        return test_runner.run_tests(tests)


@contextlib.contextmanager
def create_test_solr_core():
    # It's important to specify dataDir here, because the solrconfig.xml gives the dataDir
    # for the production core and the two can't be the same
    run_solr_admin_cmd(
            'Creating temporary Solr core...',
            'action=CREATE&name=cantus-test&instanceDir=cantus-test&dataDir=data')

    err = None

    try:
        yield
    except Exception as e:
        err = e

    run_solr_admin_cmd(
            'Unloading temporary Solr core',
            'action=UNLOAD&core=cantus-test&deleteDataDir=true')

    if err is not None:
        raise err


def run_solr_admin_cmd(msg, args):
    print>>sys.stderr, msg

    cmd = base_settings.SOLR_SERVER + '/admin/cores?' + args
    resp = requests.get(cmd)
    resp.raise_for_status()
    return resp


if __name__ == "__main__":
    main()
