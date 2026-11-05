# Grafana dashboards

Two dashboards on the metrics described in `k8s/MIGRATION.md#monitoring`. They are
imported by hand; nothing here is applied with kubectl (`kubectl apply -f
k8s/cantus-ultimus/monitoring/` does not descend into this folder).

| File | Dashboard | For |
|---|---|---|
| `cantus-service-health.json` | Cantus Ultimus — Service health | Is the site working: edge probe, HTTP errors and latency, Solr, Celery and RabbitMQ, pods and volumes. Stat thresholds match the alerts in `../alerts.yaml`. |
| `cantus-usage-content.json` | Cantus Ultimus — Usage & content | How the site is used and what it holds: readers, searches, the viewer's IIIF libraries, manuscripts, the MEI pipeline. The **Client** filter defaults to `browser`, so bots are left out unless you pick them. |

## Importing

Grafana → Dashboards → New → Import → upload the JSON → pick the **Prometheus**
data source when asked → Import. Each dashboard has a fixed uid (`cantus-health`,
`cantus-usage`), so importing a newer version over the old one replaces it.

Some panels stay empty until something happens: Celery task panels, Solr sync,
chant imports, folio mappings and the MEI review/publish panels only have data
once those events occur.
