from contextlib import contextmanager

from django.dispatch import receiver as django_receiver


# Global internal signal registry
_signal_registry = {}


def retrievable_receiver(signal, dispatch_uid, sender=None):
    """Drop-in replacement for django.dispatch.receiver (with a subset of options)

    Adds the signals to a global registry for retrieval
    """
    def register(fn):
        if dispatch_uid in _signal_registry:
            raise ValueError('a receiver with uid {} is already registered by the signal wrangler'.format(dispatch_uid))

        _signal_registry[dispatch_uid] = (signal, sender, fn)
        return django_receiver(signal, sender=sender, dispatch_uid=dispatch_uid)

    return register


@contextmanager
def signal_receivers_disconnected(*uids):
    """Context manager for managing Django signal receivers

    Takes a list of dispatch uids for receivers registered with retrievable_receiver

    Example:

    >>> with signal_receivers_disconnected('cantusdata_chant_solr_add', 'cantusdata_folio_solr_add'):
    ...     # Operate without the receivers being fired
    ...
    >>> # Receivers have automatically been reconnected
    """

    # Disconnect the receivers
    for uid in uids:
        (signal, sender, fn) = _signal_registry[uid]
        signal.disconnect(dispatch_uid=uid)

    # Execute the with statement body
    yield

    # Reconnect the receivers
    for uid in uids:
        (signal, sender, fn) = _signal_registry[uid]
        signal.connect(fn, sender=sender, dispatch_uid=uid)
