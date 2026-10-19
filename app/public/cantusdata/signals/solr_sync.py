"""
This module initializes the signal handlers which synchronize the Django DB
and Solr records, and exposes control for doing intensive DB manipulations
(relatively) efficiently:

>>> from cantusdata.signals.solr_sync import solr_synchronizer
>>> with solr_synchronizer.get_session():
...     # Create/update/destroy a bunch of Django models
...     # And Solr will be updated all at once
"""

import contextlib
import time
from collections import Counter

from django.db.models.signals import post_save, post_delete
from django.conf import settings

from ..helpers.solr_client import make_solr
from ..metrics.definitions import (
    SOLR_SYNC_DOCUMENTS,
    SOLR_SYNC_DURATION,
    SOLR_SYNC_SESSIONS,
)
from ..models import Manuscript, Chant, Folio


class SolrSynchronizer(object):
    def __init__(self, solr_server_url):
        self.solr_server_url = solr_server_url

        self._session = None
        self._targets = None
        self._handlers = self._instantiate_handlers()

    def _instantiate_handlers(self):
        handlers = [
            (Manuscript, post_save, self.folio_or_manuscript_saved),
            (Manuscript, post_delete, self.folio_or_manuscript_deleted),
            (Folio, post_save, self.folio_or_manuscript_saved),
            (Folio, post_delete, self.folio_or_manuscript_deleted),
            (Chant, post_save, self.chant_saved),
            (Chant, post_delete, self.chant_deleted),
        ]

        for model, signal, receiver in handlers:
            signal.connect(receiver, sender=model)

        return handlers

    def detach_handlers(self):
        for model, signal, receiver in self._handlers:
            signal.disconnect(receiver, sender=model)

    @contextlib.contextmanager
    def get_session(self):
        if self._session:
            if not self._session._executing_flag:
                yield self._session
                return

        self._session = SynchronizationSession(self.solr_server_url)

        try:
            yield self._session
        except Exception as e:
            raise e
        else:
            self._session.execute()
        finally:
            self._session = None

    # Handlers #

    def folio_or_manuscript_saved(self, sender, instance, created, **kwargs):
        with self.get_session() as sess:
            sess.schedule_update(instance, is_new=created)

    def folio_or_manuscript_deleted(self, sender, instance, using, **kwargs):
        with self.get_session() as sess:
            sess.schedule_deletion(instance)

    def chant_saved(self, sender, instance, created, **kwargs):
        with self.get_session() as sess:
            sess.schedule_update(instance, is_new=created)

            if created:
                sess.schedule_update(instance.folio)
                sess.schedule_update(instance.manuscript)

    def chant_deleted(self, sender, instance, using, **kwargs):
        with self.get_session() as sess:
            sess.schedule_deletion(instance)
            sess.schedule_update(instance.folio)
            sess.schedule_update(instance.manuscript)

    # The handler for this is attached in CantusdataConfig.ready
    # so that it gets run when the config is changed for tests
    def db_refresh(self, verbosity=0, **kwargs):
        if verbosity > 0:
            print("Updating Solr index after database flush or migration...")

        with self.get_session() as sess:
            sess.schedule_full_refresh()


class SynchronizationSession(object):
    def __init__(self, solr_server_url):
        self.solr_server_url = solr_server_url

        self._deletions = set()
        self._additions = set()

        self._executing_flag = False

    def execute(self):
        additions = set(self._additions)
        deletions = set(self._deletions)
        self._executing_flag = True
        started = time.perf_counter()
        outcome = "error"
        try:
            # A session can carry a whole import, or a full refresh after a
            # migration, so it gets the indexing timeout.
            conn = make_solr(
                "sync", url=self.solr_server_url, timeout=settings.SOLR_INDEX_TIMEOUT
            )

            for deleted in deletions:
                deleted.delete_from_solr(conn)

            conn.add_many([added.create_solr_record() for added in additions])
            conn.commit()
            outcome = "success"
        finally:
            SOLR_SYNC_SESSIONS.labels(outcome).inc()
            SOLR_SYNC_DURATION.observe(time.perf_counter() - started)
        for action, records in (("delete", deletions), ("add", additions)):
            for record_type, count in Counter(map(_record_type, records)).items():
                SOLR_SYNC_DOCUMENTS.labels(action, record_type).inc(count)
        self._executing_flag = False

    def schedule_update(self, model, is_new=False):
        if not is_new:
            self._deletions.add(model)

        self._additions.add(model)

    def schedule_deletion(self, model):
        # If the model's record was previously going to be updated,
        # we cancel the update
        try:
            self._additions.remove(model)
        except KeyError:
            pass

        self._deletions.add(model)

    def schedule_full_refresh(self):
        self._deletions.clear()
        self._deletions.add(DbFlusher())

        self._additions.clear()
        self._additions.update(Manuscript.objects.all())
        self._additions.update(Folio.objects.all())
        self._additions.update(Chant.objects.all())


def _record_type(record):
    return "all" if isinstance(record, DbFlusher) else type(record).__name__.lower()


class DbFlusher(object):
    def delete_from_solr(self, conn):
        conn.delete_query(
            "type:cantusdata_chant OR type:cantusdata_folio OR type:cantusdata_manuscript"
        )


solr_synchronizer = SolrSynchronizer(settings.SOLR_SERVER)
