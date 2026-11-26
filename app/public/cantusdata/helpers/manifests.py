"""
Fetching IIIF manifests for the viewer without becoming an open proxy.

The manifest proxy exists because many libraries still serve manifests over plain
http, which an https page may not fetch. It used to fetch whatever URL it was
given, so anyone could make the server request internal addresses (Solr, the
app itself) and read the answer. Now the request only names a manifest: the URL
fetched is always one stored on a manuscript, and every hop of the fetch,
redirects included, must lead to a public address.
"""

import ipaddress
import re
import socket
import time
from typing import Optional, Union
from urllib.parse import unquote, urljoin, urlsplit

import requests

MAX_REDIRECTS = 3
MAX_MANIFEST_BYTES = 20 * 1024 * 1024
# (connect, read) seconds per request, and a ceiling on the whole fetch: the
# read timeout applies per read, so a server dripping bytes would never trip it.
TIMEOUT = (5, 30)
TOTAL_DEADLINE_SECONDS = 45
# Some libraries (e-codices) drop connections that announce python-requests.
USER_AGENT = "Mozilla/5.0 (compatible; CantusUltimus/1.0; +https://cantus.simssa.ca)"

_DEFAULT_PORTS = {"http": 80, "https": 443}
_NAT64 = ipaddress.ip_network("64:ff9b::/96")

IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


class UnsafeManifestURL(Exception):
    """The fetch would leave the public internet, or break the fetch policy."""


class ManifestUnavailable(Exception):
    """The manifest's server could not be reached or sent something unusable."""


def normalize_manifest_url(url: str) -> str:
    """
    A manifest URL reduced to what survives the trip through the proxy's path.

    The scheme is dropped (the client may ask over http for an https manifest),
    percent-encoding is undone, and repeated slashes in the path are collapsed
    (Traefik collapses them). The query is kept: it can be part of what
    identifies a manifest.
    """
    url = unquote(url.strip())
    url = re.sub(r"^https?:/*", "", url, flags=re.IGNORECASE)
    url = url.split("#", 1)[0]
    path, separator, query = url.partition("?")
    path = re.sub(r"/{2,}", "/", path).rstrip("/")
    return f"{path}{separator}{query}" if query else path


def find_known_manifest(requested: str) -> Optional[tuple[int, str]]:
    """
    (manuscript id, stored URL) of the manifest `requested` names, or None.

    None also when the request matches more than one distinct stored URL: an
    ambiguous request is not allowed to choose for itself. Queried every time
    (a few dozen rows) so that a manifest added in the admin works at once.
    """
    # Imported here: helpers are imported while the app registry loads.
    from cantusdata.models.manuscript import Manuscript

    key = normalize_manifest_url(requested)
    matches: dict[str, int] = {}
    rows = (
        Manuscript.objects.exclude(manifest_url__isnull=True)
        .exclude(manifest_url="")
        .values_list("pk", "manifest_url")
    )
    for pk, stored in rows:
        if normalize_manifest_url(stored) == key:
            matches[stored.strip()] = pk
    if len(matches) != 1:
        return None
    ((url, pk),) = matches.items()
    return pk, url


def _is_public(address: IPAddress) -> bool:
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        elif address in _NAT64:
            # NAT64 embeds an IPv4 address in the low 32 bits, and counts as
            # "global" even when that address is 127.0.0.1.
            address = ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
    return address.is_global and not address.is_multicast


def _check_hop(url: str, stored_port: int) -> None:
    """Refuse a hop that is not plain http(s) to a public address."""
    parts = urlsplit(url)
    if parts.scheme not in _DEFAULT_PORTS:
        raise UnsafeManifestURL(f"scheme {parts.scheme!r} is not allowed")
    if parts.username or parts.password:
        raise UnsafeManifestURL("credentials in the URL are not allowed")
    try:
        port = parts.port or _DEFAULT_PORTS[parts.scheme]
    except ValueError as exc:
        raise UnsafeManifestURL("invalid port") from exc
    if port not in (_DEFAULT_PORTS[parts.scheme], stored_port):
        raise UnsafeManifestURL(f"port {port} is not allowed")
    if not parts.hostname:
        raise UnsafeManifestURL("no host")
    try:
        addresses = socket.getaddrinfo(parts.hostname, port, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError) as exc:
        raise ManifestUnavailable(f"cannot resolve {parts.hostname}") from exc
    for *_, sockaddr in addresses:
        try:
            # Drop an IPv6 zone index ("fe80::1%eth0") before parsing.
            address = ipaddress.ip_address(str(sockaddr[0]).split("%", 1)[0])
        except ValueError as exc:
            raise UnsafeManifestURL("unparseable address") from exc
        if not _is_public(address):
            raise UnsafeManifestURL(f"{parts.hostname} resolves to {address}")


def _read_capped(response: requests.Response, deadline: float) -> bytes:
    # iter_content decompresses, so the cap also stops a gzip bomb.
    chunks, size = [], 0
    try:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            size += len(chunk)
            if size > MAX_MANIFEST_BYTES:
                raise ManifestUnavailable("manifest is larger than allowed")
            if time.monotonic() > deadline:
                raise ManifestUnavailable("manifest took too long to download")
            chunks.append(chunk)
    except requests.RequestException as exc:
        raise ManifestUnavailable(str(exc)) from exc
    return b"".join(chunks)


def fetch_manifest(url: str) -> bytes:
    """
    The body of the manifest at `url`, a URL stored on a manuscript.

    Redirects are followed here rather than by requests, so that every hop is
    checked: a library's domain that lapses, or a redirect it was tricked into,
    must not lead into the cluster.
    """
    stored_parts = urlsplit(url)
    stored_port = stored_parts.port or _DEFAULT_PORTS.get(stored_parts.scheme, 0)
    deadline = time.monotonic() + TOTAL_DEADLINE_SECONDS
    with requests.Session() as session:
        # No proxies from the environment (they would bypass the address
        # check) and no credentials from ~/.netrc.
        session.trust_env = False
        for _ in range(MAX_REDIRECTS + 1):
            _check_hop(url, stored_port)
            try:
                response = session.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=TIMEOUT,
                    allow_redirects=False,
                    stream=True,
                )
            except requests.RequestException as exc:
                raise ManifestUnavailable(str(exc)) from exc
            with response:
                if response.is_redirect:
                    url = urljoin(url, response.headers["Location"])
                    continue
                if not response.ok:
                    raise ManifestUnavailable(f"status {response.status_code}")
                return _read_capped(response, deadline)
    raise UnsafeManifestURL(f"more than {MAX_REDIRECTS} redirects")
