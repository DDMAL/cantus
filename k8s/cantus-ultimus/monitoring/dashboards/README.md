# Grafana dashboards

Two dashboards on the metrics described in `k8s/MIGRATION.md#monitoring`. They are
imported by hand; nothing here is applied with kubectl (`kubectl apply -f
k8s/cantus-ultimus/monitoring/` does not descend into this folder).

| File | Dashboard | For |
|---|---|---|
| `cantus-service-health.json` | Cantus Ultimus — Service health | Is the site working: edge probe, HTTP errors and latency, Solr, Celery and RabbitMQ, pods and volumes. Stat thresholds match the alerts in `../alerts.yaml`. |
| `cantus-usage-content.json` | Cantus Ultimus — Usage & content | How the site is used and what it holds: readers, searches, the viewer's IIIF libraries, manuscripts, the MEI pipeline. The **Client** filter defaults to `browser`, so bots are left out unless you pick them. |

The files are in Grafana's v2 dashboard format (`elements`, `layout`, `variables`),
which Grafana 13 expects; the classic format (`panels`, `templating`) fails its
validation with `Missing property "variables"`.

## Importing

Grafana → Dashboards → New → Import → upload the JSON. On the form, click
**Change uid** and set `cantus-health` or `cantus-usage` (a v2 file carries no uid,
so without this Grafana picks a random one and the dashboard's URL changes with
every fresh import) → Import.

To update a dashboard later, import the new file the same way with the same uid:
Grafana offers **Import (Overwrite)** and replaces it in place.

There is no data source prompt: queries use the dashboard's **Data source**
variable, which defaults to the data source with uid `prometheus` (the cluster's
Prometheus) and can be switched from the dashboard's toolbar.

Each dashboard links to the other through a tag link (`cantus-ultimus`), so the
link works whatever the uids are.

Some panels stay empty until something happens: Celery task panels, Solr sync,
chant imports, folio mappings and the MEI review/publish panels only have data
once those events occur.
