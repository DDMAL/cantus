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
import solr

from django.db.models.signals import post_save, post_delete
from django.conf import settings

from ..models import Manuscript, Chant, Folio


class SolrSynchronizer (object):
    def __init__(self, solr_server_url):
        self.solr_server_url = solr_server_url

        self._session = None
        self._targets = None
        self._handlers = self._instantiate_handlers()

    def _instantiate_handlers(self):
        handlers = [
            (Manuscript, post_save,   self.folio_or_manuscript_saved),
            (Manuscript, post_delete, self.folio_or_manuscript_deleted),
            (Folio,      post_save,   self.folio_or_manuscript_saved),
            (Folio,      post_delete, self.folio_or_manuscript_deleted),
            (Chant,      post_save,   self.chant_saved),
            (Chant,      post_delete, self.chant_deleted),
        ]

        for (model, signal, receiver) in handlers:
            signal.connect(receiver, sender=model)

        return handlers

    def detach_handlers(self):
        for (model, signal, receiver) in self._handlers:
            signal.disconnect(receiver, sender=model)

    @contextlib.contextmanager
    def get_session(self):
        if self._session:
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

    def folio_or_manuscript_deleted(self, sender, instance, **kwargs):
        with self.get_session() as sess:
            sess.schedule_deletion(instance)

    def chant_saved(self, sender, instance, created, **kwargs):
        with self.get_session() as sess:
            sess.schedule_update(instance, is_new=created)

            if created:
                sess.schedule_update(instance.folio)
                sess.schedule_update(instance.manuscript)

    def chant_deleted(self, sender, instance, **kwargs):
        with self.get_session() as sess:
            sess.schedule_deletion(instance)
            sess.schedule_update(instance.folio)
            sess.schedule_update(instance.manuscript)

    # The handler for this is attached in CantusdataConfig.ready
    # so that it gets run when the config is changed for tests
    def db_flushed(self, **kwargs):
        assert Chant.objects.all().count() == 0
        assert Folio.objects.all().count() == 0
        assert Manuscript.objects.all().count() == 0

        with self.get_session() as sess:
            sess.schedule_full_flush()


class SynchronizationSession (object):
    def __init__(self, solr_server_url):
        self.solr_server_url = solr_server_url

        self._deletions = set()
        self._additions = set()

    def execute(self):
        conn = solr.SolrConnection(self.solr_server_url)

        for deleted in self._deletions:
            deleted.delete_from_solr(conn)

        conn.add_many([added.create_solr_record() for added in self._additions])
        conn.commit()

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

    def schedule_full_flush(self):
        self._additions.clear()
        self._deletions.clear()
        self._deletions.add(DbFlusher())


class DbFlusher (object):
    def delete_from_solr(self, conn):
        conn.delete_query('type:cantusdata_chant OR type:cantusdata_folio OR type:cantusdata_manuscript')


solr_synchronizer = SolrSynchronizer(settings.SOLR_SERVER)
