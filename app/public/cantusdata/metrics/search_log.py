"""
One JSON line on stdout per search, for questions metrics cannot answer -- what
people search for. Metrics only ever see the shape of a search.

Deliberately carries no IP address, user agent or user: the term and its context
are enough to learn which chants, feasts and melodies researchers look for.
Django's logging is not configured (LOGGING_CONFIG = None), so this logger sets
up its own handler and does not propagate.
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from django.conf import settings

MAX_TERM_LENGTH = 200

logger = logging.getLogger("cantusdata.search")

# The manuscript restriction the client appends to scoped chant searches; the
# manuscript is logged as its own field instead.
_MANUSCRIPT_RESTRICTION = re.compile(r'(?:\s+AND\s+)?manuscript_id:"?\d+"?')


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "event": record.getMessage(),
            **getattr(record, "search", {}),
        }
        return json.dumps(event, ensure_ascii=False)


def configure() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def normalize_term(term: str) -> str:
    term = _MANUSCRIPT_RESTRICTION.sub("", term).replace("_t_hidden:", ":")
    return " ".join(term.lower().split())[:MAX_TERM_LENGTH]


def log_search(
    kind: str,
    *,
    field: str,
    term: str,
    manuscript_id: Optional[Any],
    num_found: Optional[int],
    client: str,
    duration_ms: float,
) -> None:
    if not getattr(settings, "SEARCH_EVENT_LOG", True):
        return
    logger.info(
        "search",
        extra={
            "search": {
                "kind": kind,
                "field": field,
                "term": normalize_term(term),
                "manuscript_id": manuscript_id,
                "num_found": num_found,
                "client": client,
                "duration_ms": round(duration_ms, 1),
            }
        },
    )
