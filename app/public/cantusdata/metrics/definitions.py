"""
All of Cantus Ultimus' own metrics, in one place.

Counters are declared with their `_total` suffix so the exposed name is what a
grep of this file finds; prometheus_client accepts either spelling. Gauges that
several processes write declare a multiprocess_mode: it is ignored outside
multiprocess mode and required to merge them correctly inside it.
"""

from prometheus_client import Counter, Gauge, Histogram

# Buckets ---------------------------------------------------------------------

HTTP_LATENCY_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2.5,
    5,
    10,
    30,
    60,
    120,
    300,
    600,
)
DEPENDENCY_LATENCY_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2.5,
    5,
    10,
    30,
    60,
    120,
)
DB_LATENCY_BUCKETS = (
    0.001,
    0.0025,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1,
    2.5,
    5,
    10,
)
SIZE_BUCKETS = (1e3, 1e4, 1e5, 5e5, 1e6, 5e6, 1e7, 5e7)
QUERY_COUNT_BUCKETS = (0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)
RESULT_COUNT_BUCKETS = (0, 1, 5, 20, 50, 100, 500, 1000, 5000, 10000)
# The chant search client loads 20 rows at a time, up to 100 before it waits
# for the reader to scroll (ChantSearchProvider.js).
RESULT_OFFSET_BUCKETS = (0, 20, 40, 60, 80, 100, 200, 500)
NOTATION_QUERY_LENGTH_BUCKETS = (1, 2, 3, 4, 5, 6, 8, 10, 15, 20)
TASK_DURATION_BUCKETS = (1, 5, 15, 30, 60, 120, 300, 600, 1800, 3600, 7200, 14400)
TASK_QUEUE_WAIT_BUCKETS = (0.1, 0.5, 1, 5, 15, 60, 300, 900, 3600, 14400)
HOUR = 3600
DAY = 24 * HOUR
REVIEW_LATENCY_BUCKETS = (
    HOUR,
    6 * HOUR,
    DAY,
    3 * DAY,
    7 * DAY,
    14 * DAY,
    30 * DAY,
    90 * DAY,
)

# Build -----------------------------------------------------------------------

BUILD_INFO = Gauge(
    "cantus_build_info",
    "Always 1; labels identify the running build.",
    ["git_sha", "django", "python"],
    multiprocess_mode="max",
)

# HTTP ------------------------------------------------------------------------

HTTP_REQUESTS = Counter(
    "cantus_http_requests_total",
    "HTTP requests handled by Django.",
    ["method", "route", "status", "client"],
)
HTTP_REQUEST_DURATION = Histogram(
    "cantus_http_request_duration_seconds",
    "Time Django spent producing a response.",
    ["method", "route"],
    buckets=HTTP_LATENCY_BUCKETS,
)
HTTP_RESPONSE_SIZE = Histogram(
    "cantus_http_response_size_bytes",
    "Size of non-streaming response bodies.",
    ["route"],
    buckets=SIZE_BUCKETS,
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "cantus_http_requests_in_progress",
    "Requests currently being handled, summed over live workers.",
    multiprocess_mode="livesum",
)
HTTP_EXCEPTIONS = Counter(
    "cantus_http_exceptions_total",
    "Exceptions that escaped a view (DRF-handled API errors are not counted).",
    ["route", "exception"],
)
HTTP_REQUEST_DB_QUERIES = Histogram(
    "cantus_http_request_db_queries",
    "Database queries issued while handling one request.",
    ["route"],
    buckets=QUERY_COUNT_BUCKETS,
)
PAGE_LOADS = Counter(
    "cantus_page_loads_total",
    "Full HTML page loads (the single-page app's shell or a static page).",
    ["page", "client"],
)

# Gunicorn --------------------------------------------------------------------

GUNICORN_WORKERS = Gauge(
    "cantus_gunicorn_workers",
    "Configured number of gunicorn worker processes.",
    multiprocess_mode="max",
)
GUNICORN_WORKER_EXITS = Counter(
    "cantus_gunicorn_worker_exits_total",
    "Gunicorn worker processes that exited (crashed, killed or recycled).",
)
GUNICORN_WORKER_TIMEOUTS = Counter(
    "cantus_gunicorn_worker_timeouts_total",
    "Gunicorn workers aborted for exceeding the request timeout.",
)

# Database --------------------------------------------------------------------

DB_QUERIES = Counter(
    "cantus_db_queries_total",
    "Database queries executed.",
    ["operation", "outcome"],
)
DB_QUERY_DURATION = Histogram(
    "cantus_db_query_duration_seconds",
    "Database query execution time.",
    ["operation"],
    buckets=DB_LATENCY_BUCKETS,
)
DB_ERRORS = Counter(
    "cantus_db_errors_total",
    "Database queries that raised, by exception class.",
    ["error"],
)

# Solr ------------------------------------------------------------------------

SOLR_REQUESTS = Counter(
    "cantus_solr_requests_total",
    "HTTP requests made to Solr.",
    ["operation", "outcome"],
)
SOLR_REQUEST_DURATION = Histogram(
    "cantus_solr_request_duration_seconds",
    "Duration of HTTP requests made to Solr, including client retries.",
    ["operation"],
    buckets=DEPENDENCY_LATENCY_BUCKETS,
)
SOLR_SYNC_SESSIONS = Counter(
    "cantus_solr_sync_sessions_total",
    "Batches of database changes pushed to Solr by the sync signals.",
    ["outcome"],
)
SOLR_SYNC_DOCUMENTS = Counter(
    "cantus_solr_sync_documents_total",
    "Records the sync signals added to or deleted from Solr.",
    ["action", "record_type"],
)
SOLR_SYNC_DURATION = Histogram(
    "cantus_solr_sync_duration_seconds",
    "Time to push one batch of database changes to Solr.",
    buckets=DEPENDENCY_LATENCY_BUCKETS + (300,),
)

# External HTTP ---------------------------------------------------------------

EXTERNAL_REQUESTS = Counter(
    "cantus_external_requests_total",
    "HTTP requests made to services outside the cluster.",
    ["target", "upstream_host", "outcome"],
)
EXTERNAL_REQUEST_DURATION = Histogram(
    "cantus_external_request_duration_seconds",
    "Duration of HTTP requests made to services outside the cluster.",
    ["target"],
    buckets=DEPENDENCY_LATENCY_BUCKETS,
)

# Celery ----------------------------------------------------------------------

CELERY_TASKS_PUBLISHED = Counter(
    "cantus_celery_tasks_published_total",
    "Tasks sent to the broker.",
    ["task"],
)
CELERY_TASKS_RECEIVED = Counter(
    "cantus_celery_tasks_received_total",
    "Tasks a worker received from the broker.",
    ["task"],
)
CELERY_TASK_RUNS = Counter(
    "cantus_celery_task_runs_total",
    "Task executions by outcome.",
    ["task", "outcome"],
)
CELERY_TASK_DURATION = Histogram(
    "cantus_celery_task_duration_seconds",
    "Task execution time.",
    ["task"],
    buckets=TASK_DURATION_BUCKETS,
)
CELERY_TASK_QUEUE_WAIT = Histogram(
    "cantus_celery_task_queue_wait_seconds",
    "Time between a task being published and a worker starting it.",
    ["task"],
    buckets=TASK_QUEUE_WAIT_BUCKETS,
)
CELERY_TASKS_IN_PROGRESS = Gauge(
    "cantus_celery_tasks_in_progress",
    "Tasks currently executing.",
    ["task"],
    multiprocess_mode="livesum",
)

# Business: traffic -----------------------------------------------------------

MANUSCRIPT_VIEWS = Counter(
    "cantus_manuscript_views_total",
    "Manuscripts opened in the viewer (one manuscript-detail JSON fetch each).",
    ["manuscript_id", "client"],
)
FOLIO_VIEWS = Counter(
    "cantus_folio_views_total",
    "Folios displayed in the viewer (one image-to-folio lookup per page turn).",
    ["manuscript_id", "client"],
)
FOLIO_CHANT_LOOKUPS = Counter(
    "cantus_folio_chant_lookups_total",
    "Chant lists fetched for a displayed folio, by whether it had any chants.",
    ["manuscript_id", "has_chants"],
)
VIEWER_MANIFEST_LOADS = Counter(
    "cantus_viewer_manifest_loads_total",
    "IIIF manifests fetched through the manifest proxy for the viewer.",
    ["manuscript_id", "outcome"],
)

# Business: search ------------------------------------------------------------

SEARCH_REQUESTS = Counter(
    "cantus_search_requests_total",
    "Chant searches (first page of results only).",
    ["field", "scope", "outcome", "client"],
)
SEARCH_RESULTS = Histogram(
    "cantus_search_results",
    "Number of chants matching a search.",
    ["field"],
    buckets=RESULT_COUNT_BUCKETS,
)
SEARCH_RESULT_OFFSET = Histogram(
    "cantus_search_result_offset",
    "Offset of each page of chant search results requested.",
    buckets=RESULT_OFFSET_BUCKETS,
)
NOTATION_SEARCH_REQUESTS = Counter(
    "cantus_notation_search_requests_total",
    "Notation (OMR) searches.",
    ["type", "manuscript_id", "outcome", "client"],
)
NOTATION_SEARCH_QUERY_LENGTH = Histogram(
    "cantus_notation_search_query_length",
    "Number of elements (neumes, pitches, ...) in a notation search.",
    ["type"],
    buckets=NOTATION_QUERY_LENGTH_BUCKETS,
)
NOTATION_SEARCH_RESULTS = Histogram(
    "cantus_notation_search_results",
    "Number of matches for a notation search.",
    ["type"],
    buckets=RESULT_COUNT_BUCKETS,
)
SUGGEST_REQUESTS = Counter(
    "cantus_suggest_requests_total",
    "Search-as-you-type suggestion requests.",
    ["field", "outcome"],
)

# Business: MEI deposit pipeline ----------------------------------------------

MEI_SUBMISSIONS_RECEIVED = Counter(
    "cantus_mei_submissions_received_total",
    "MEI deposits received over the API.",
    ["outcome", "reason", "account"],
)
MEI_SUBMISSION_SIZE = Histogram(
    "cantus_mei_submission_size_bytes",
    "Size of deposited MEI documents.",
    buckets=(1e4, 5e4, 1e5, 2.5e5, 5e5, 1e6, 2.5e6, 5e6),
)
MEI_SUBMISSIONS_SUPERSEDED = Counter(
    "cantus_mei_submissions_superseded_total",
    "Pending submissions replaced by a newer deposit for the same folio.",
)
MEI_REVIEWS = Counter(
    "cantus_mei_reviews_total",
    "Review decisions taken in the admin.",
    ["action", "via"],
)
MEI_REVIEW_LATENCY = Histogram(
    "cantus_mei_review_latency_seconds",
    "Time from a submission arriving to its review decision.",
    ["action"],
    buckets=REVIEW_LATENCY_BUCKETS,
)
MEI_PUBLISH = Counter(
    "cantus_mei_publish_total",
    "Publication task runs by outcome.",
    ["outcome"],
)
MEI_PUBLISH_DURATION = Histogram(
    "cantus_mei_publish_duration_seconds",
    "Time to write and index one published submission.",
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

# Business: data operations, admin, security ----------------------------------

CHANT_IMPORT_RUNS = Counter(
    "cantus_chant_import_runs_total",
    "Chant imports from CANTUS Database, by outcome.",
    ["outcome"],
)
CHANTS_IMPORTED = Counter(
    "cantus_chants_imported_total",
    "Chants imported from CANTUS Database.",
    ["manuscript_id"],
)
FOLIO_MAPPING_RUNS = Counter(
    "cantus_folio_mapping_runs_total",
    "Folio-to-image mapping runs, by outcome.",
    ["outcome"],
)
FOLIOS_MAPPED = Counter(
    "cantus_folios_mapped_total",
    "Folios assigned an image by a mapping run.",
    ["manuscript_id"],
)
NEUME_EXEMPLAR_SAVES = Counter(
    "cantus_neume_exemplar_saves_total",
    "Neume exemplar sets saved from the admin.",
    ["manuscript_id"],
)
ADMIN_LOGINS = Counter(
    "cantus_admin_logins_total",
    "Admin login attempts by outcome.",
    ["outcome"],
)
BACKGROUND_THREAD_FAILURES = Counter(
    "cantus_background_thread_failures_total",
    "Work started in a background thread that raised.",
    ["thread"],
)
