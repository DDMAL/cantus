"""
Bounded label values.

A label value that comes from a request -- an id in the URL, a query string, a
URL passed to the manifest proxy -- would let any client mint new time series.
Everything here maps such input onto a small fixed set, or onto values checked
against the database, and falls back to OTHER.
"""

import re
import threading
import time
from typing import Any, Optional
from urllib.parse import urlsplit

OTHER = "other"

# Client classification -------------------------------------------------------

# The blackbox exporter sends "Blackbox-Exporter/0.28.0"; older versions a space.
_PROBE_AGENTS = re.compile(r"kube-probe|blackbox[- ]exporter|prometheus", re.IGNORECASE)
_BOT_AGENTS = re.compile(
    r"bot|crawl|spider|slurp|archiver|facebookexternalhit|curl|wget|"
    r"python-requests|python-urllib|httpx|aiohttp|go-http-client|java/|okhttp|"
    r"libwww|scrapy|headless|phantomjs|semrush|ahrefs|bytespider|"
    r"gptbot|claudebot|ccbot|perplexity",
    re.IGNORECASE,
)


def classify_client(request: Any) -> str:
    """
    One of api, probe, bot or browser.

    `api` is anything authenticating with a DRF token -- the MEI deposit
    pipeline today. Probes are checked before bots because monitoring user agents
    would otherwise match the generic patterns.
    """
    meta = request.META
    if meta.get("HTTP_AUTHORIZATION", "").startswith("Token "):
        return "api"
    agent = meta.get("HTTP_USER_AGENT", "")
    if _PROBE_AGENTS.search(agent):
        return "probe"
    if not agent or _BOT_AGENTS.search(agent):
        return "bot"
    return "browser"


# Routes ----------------------------------------------------------------------

_HTTP_METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}


def method_label(request: Any) -> str:
    return request.method if request.method in _HTTP_METHODS else OTHER


def route_label(request: Any) -> str:
    """
    The URL pattern's name. Every pattern in urls.py is named, and the
    format-suffix variants share their base pattern's name. The admin's many
    routes collapse into one value.
    """
    match = getattr(request, "resolver_match", None)
    if match is None:
        return "unmatched"
    if "admin" in match.namespaces:
        return "admin"
    return match.url_name or "unnamed"


# Manuscripts -----------------------------------------------------------------


class _PublicManuscripts:
    """
    A per-process snapshot of public manuscripts, refreshed every few minutes.

    Kept per process (each gunicorn worker has its own) because the alternative,
    a query per labelled event, would put a database round trip on every search.
    """

    TTL_SECONDS = 300

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # None until the first load. Not 0.0: time.monotonic() counts from
        # boot, so on a machine up for less than TTL_SECONDS a zero would look
        # fresh and the snapshot would never load.
        self._loaded_at: Optional[float] = None
        self._ids: frozenset[str] = frozenset()
        self._manifest_hosts: frozenset[str] = frozenset()

    def _is_fresh(self) -> bool:
        return (
            self._loaded_at is not None
            and time.monotonic() - self._loaded_at < self.TTL_SECONDS
        )

    def _refresh_if_stale(self) -> None:
        if self._is_fresh():
            return
        with self._lock:
            if self._is_fresh():
                return
            # Imported here: labels is imported while the app registry loads.
            from cantusdata.models.manuscript import Manuscript

            try:
                rows = list(
                    Manuscript.objects.filter(public=True).values_list(
                        "pk", "manifest_url"
                    )
                )
            except Exception:  # pylint: disable=broad-exception-caught
                # A label is never worth failing a request over. Keep the last
                # snapshot and try again on the next call.
                return
            self._ids = frozenset(str(pk) for pk, _ in rows)
            self._manifest_hosts = frozenset(
                host for _, url in rows if url and (host := _hostname(url))
            )
            self._loaded_at = time.monotonic()

    def id_label(self, manuscript_id: Any) -> str:
        self._refresh_if_stale()
        value = str(manuscript_id)
        return value if value in self._ids else OTHER

    def is_manifest_host(self, host: str) -> bool:
        self._refresh_if_stale()
        return host in self._manifest_hosts

    def reset(self) -> None:
        """Forget the snapshot (for tests, which create manuscripts)."""
        self._loaded_at = None


public_manuscripts = _PublicManuscripts()


def manuscript_label(manuscript_id: Any) -> str:
    """The id itself if it names a public manuscript, else OTHER."""
    return public_manuscripts.id_label(manuscript_id)


def _hostname(url: str) -> Optional[str]:
    try:
        return urlsplit(url).hostname
    except ValueError:
        return None


KNOWN_EXTERNAL_HOSTS = frozenset({"cantusdatabase.org"})


def upstream_host_label(url: str) -> str:
    """The host of `url` if Cantus Ultimus is known to talk to it, else OTHER."""
    host = _hostname(url)
    if host is None:
        return OTHER
    if host in KNOWN_EXTERNAL_HOSTS or public_manuscripts.is_manifest_host(host):
        return host
    return OTHER


# Chant search ----------------------------------------------------------------

# The fields the chant search can query. The client searches the tokenized
# "_t_hidden" copy of string fields (ChantSearchProvider.getSearchField), so that
# suffix is stripped before matching.
SEARCH_FIELDS = frozenset(
    {
        "manuscript",
        "volpiano",
        "volpiano_literal",
        "mode",
        "feast",
        "genre",
        "office",
        "position",
        "incipit",
        "differentia",
        "differentiae_database",
        "finalis",
        "folio",
        "cantus_id",
        "full_text",
        "full_text_ms",
    }
)
# A field name at the start of the query or of a term. Escaped colons inside
# values ("\:") are not preceded by a bare word, so they don't match.
_QUERY_FIELD = re.compile(r"(?:^|[\s(])([A-Za-z_]+):")


def parse_search_query(query: str) -> tuple[str, str]:
    """
    (field, scope) for a chant search query string as the client builds it
    (SolrQuery.toString): `<term> AND field:value AND manuscript_id:"<id>"`.

    field is `all` for a free-text search, the field name for a fielded search,
    `multi` when several fields are combined, or OTHER. scope is `manuscript`
    when the search is restricted to one manuscript, else `global`.
    """
    names = {
        name[: -len("_t_hidden")] if name.endswith("_t_hidden") else name
        for name in _QUERY_FIELD.findall(query)
    }
    scope = "manuscript" if "manuscript_id" in names else "global"
    names.discard("manuscript_id")
    if not names:
        return "all", scope
    if len(names) > 1:
        return "multi", scope
    (name,) = names
    return (name if name in SEARCH_FIELDS else OTHER), scope


_MANUSCRIPT_RESTRICTION = re.compile(r'manuscript_id:"?(\d+)')


def search_manuscript_id(query: str) -> Optional[str]:
    """The manuscript a chant search is restricted to, if any."""
    match = _MANUSCRIPT_RESTRICTION.search(query)
    return match.group(1) if match else None


NOTATION_SEARCH_TYPES = frozenset(
    {"neume_names", "pitch_names", "pitch_names_transposed", "contour", "intervals"}
)


def notation_type_label(search_type: Optional[str]) -> str:
    return search_type if search_type in NOTATION_SEARCH_TYPES else "invalid"
