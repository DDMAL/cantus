# Cantus Ultimus — Kubernetes Migration Plan

## Prerequisites

- `kubectl` configured and pointing at the target cluster
- Docker and `docker compose` available on the source machine
- Images built and pushed to `ghcr.io/ddmal/cantus-*`
- All `<value>` placeholders in secret files filled in

---

## 1. Build and Push Images

```bash
# Build all images from project root
docker build --build-arg DEVELOPMENT=False -f app/Dockerfile \
  -t ghcr.io/ddmal/cantus-app:main-latest .
docker build -f nginx/Dockerfile \
  -t ghcr.io/ddmal/cantus-nginx:main-latest .
docker build -f solr/Dockerfile \
  -t ghcr.io/ddmal/cantus-solr:main-latest ./solr
docker build -f rabbitmq/Dockerfile \
  -t ghcr.io/ddmal/cantus-rabbitmq:main-latest ./rabbitmq
docker build -f cantaloupe/Dockerfile \
  -t ghcr.io/ddmal/cantus-cantaloupe:main-latest ./cantaloupe

docker push ghcr.io/ddmal/cantus-app:main-latest
docker push ghcr.io/ddmal/cantus-nginx:main-latest
docker push ghcr.io/ddmal/cantus-solr:main-latest
docker push ghcr.io/ddmal/cantus-rabbitmq:main-latest
docker push ghcr.io/ddmal/cantus-cantaloupe:main-latest
```

Or trigger the GitHub Actions workflow by pushing to `main`.

---

## 2. Create Namespaces

```bash
kubectl create namespace cantus-ultimus
kubectl create namespace postgres   # skip if already exists
```

---

## 3. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres/
kubectl rollout status statefulset/postgres-cantus-ultimus -n postgres
```

Verify:
```bash
kubectl exec -n postgres \
  $(kubectl get pod -n postgres -l app=postgres-cantus-ultimus -o jsonpath='{.items[0].metadata.name}') \
  -- pg_isready -U cantus_admin -d cantus_db
```

---

## 4. Copy Database from Running Docker Compose Server

Run on the **source machine** where Docker Compose is running:

```bash
# Dump the production database
docker compose exec -T postgres \
  pg_dump -U cantus_admin cantus_db > /tmp/cantus_db_backup.sql
```

Copy and restore into the k8s postgres pod:

```bash
# Get the postgres pod name
POSTGRES_POD=$(kubectl get pod -n postgres \
  -l app=postgres-cantus-ultimus -o jsonpath='{.items[0].metadata.name}')

# Copy the dump into the pod
kubectl cp /tmp/cantus_db_backup.sql postgres/$POSTGRES_POD:/tmp/cantus_db_backup.sql

# Restore
kubectl exec -n postgres $POSTGRES_POD -- \
  psql -U cantus_admin -d cantus_db -f /tmp/cantus_db_backup.sql
```

---

## 5. Apply imagePullSecret

Fill in `k8s/cantus-ultimus/ghcr-pull-secret.yaml` with a valid GitHub classic PAT
(requires `read:packages` scope), then:

```bash
kubectl apply -f k8s/cantus-ultimus/ghcr-pull-secret.yaml
```

---

## 6. Deploy Services

Apply in dependency order:

```bash
# 1. RabbitMQ (Celery depends on it)
kubectl apply -f k8s/cantus-ultimus/rabbitmq/

# 2. Solr
kubectl apply -f k8s/cantus-ultimus/solr/

# 3. Cantaloupe (nginx proxies to it)
kubectl apply -f k8s/cantus-ultimus/cantaloupe/

# 4. MEI files volume (app and celery both mount it) -- see MEI_FILES.md for
#    the NFS export and permissions it needs on the storage server first
kubectl apply -f k8s/cantus-ultimus/mei-files-pv.yaml
kubectl apply -f k8s/cantus-ultimus/mei-files-pvc.yaml

kubectl apply -f k8s/cantus-ultimus/app/
# run migrate in the pod after the pod is ready
# NOTE: applying the whole app/ directory is correct HERE, on a fresh cluster,
# because the Prerequisites above had you fill in secret.yaml's <value>
# placeholders first. Never re-run it against a cluster that is already serving:
# the repo copy is a template, so it would overwrite the live app-secret with
# those placeholders and break the database and broker at the next pod restart.
# To change a running deployment, name the file: see k8s/MEI_FILES.md#applying.

# 5. Celery
kubectl apply -f k8s/cantus-ultimus/celery/

# 6. Nginx + Ingress
kubectl apply -f k8s/cantus-ultimus/nginx/
```

Wait for the app to become ready:
```bash
kubectl rollout status deployment/app -n cantus-ultimus
```
---

## 7. Copy PVC Data

### Cantaloupe images

```bash
CANTALOUPE_POD=$(kubectl get pod -n cantus-ultimus \
  -l app=cantaloupe -o jsonpath='{.items[0].metadata.name}')

kubectl cp ./cantaloupe/interim_files/images/. \
  cantus-ultimus/$CANTALOUPE_POD:/srv/images/
```

### IIIF manifests (nginx)

```bash
NGINX_POD=$(kubectl get pod -n cantus-ultimus \
  -l app=nginx -o jsonpath='{.items[0].metadata.name}')

kubectl cp ./cantaloupe/interim_files/manifests/. \
  cantus-ultimus/$NGINX_POD:/code/manifests/
```

> If the manifests volume is read-only, copy to a temp location on the k3s node
> and symlink, or use a temporary loader pod.

---

## 8. Import Data from CantusDB

If you restored the database from a dump (step 4), this step is only needed to
refresh data that has changed since the dump was taken. For a fresh deployment
with no dump, run the full import.

Open a shell on the app pod:

```bash
kubectl exec -it -n cantus-ultimus \
  $(kubectl get pod -n cantus-ultimus -l app=app -o jsonpath='{.items[0].metadata.name}') \
  -- python manage.py shell_plus
```

Then in the shell:

```python
from django.core.management import call_command

# Import all manuscripts
call_command("import_data", "manuscripts")

# Import chants for each manuscript (replace IDs as needed)
for ms_id in [123, 456, 789]:
    call_command("import_data", "chants", manuscript_id=ms_id)

# Import IIIF manifest URLs
call_command("import_data", "iiif")
```

---

## 9. Import Folio Mapping

Export the mapping from the running Docker Compose server:

```python
# On source server: docker compose exec app python manage.py shell_plus
import csv
from cantusdata.models.folio import Folio

folios = Folio.objects.filter(image_uri__isnull=False).exclude(image_uri="") \
    .values("manuscript_id", "number", "image_uri")

with open("/tmp/folio_mapping_export.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["manuscript_id", "folio", "uri"])
    writer.writeheader()
    for folio in folios:
        writer.writerow({
            "manuscript_id": folio["manuscript_id"],
            "folio": folio["number"],
            "uri": folio["image_uri"],
        })
```

Copy into the k8s app pod and import:

```bash
APP_POD=$(kubectl get pod -n cantus-ultimus \
  -l app=app -o jsonpath='{.items[0].metadata.name}')

kubectl cp /tmp/folio_mapping_export.csv \
  cantus-ultimus/$APP_POD:/code/folio_mapping_export.csv
```

Then in `shell_plus` on the k8s pod:

```python
import csv
from collections import defaultdict
from django.core.management import call_command

mapping = defaultdict(list)
with open("/code/folio_mapping_export.csv") as f:
    for row in csv.DictReader(f):
        mapping[row["manuscript_id"]].append({
            "folio": row["folio"],
            "uri": row["uri"],
        })

for manuscript_id, data in mapping.items():
    call_command("import_folio_mapping",
                 manuscripts=[manuscript_id],
                 mapping_data=[data])
```

---

## 10. Refresh Solr

If data was imported outside of Django signals (e.g. direct DB restore), resync Solr:

```bash
kubectl exec -n cantus-ultimus \
  $(kubectl get pod -n cantus-ultimus -l app=app -o jsonpath='{.items[0].metadata.name}') \
  -- python manage.py refresh_solr manuscripts

kubectl exec -n cantus-ultimus \
  $(kubectl get pod -n cantus-ultimus -l app=app -o jsonpath='{.items[0].metadata.name}') \
  -- python manage.py refresh_solr folios

kubectl exec -n cantus-ultimus \
  $(kubectl get pod -n cantus-ultimus -l app=app -o jsonpath='{.items[0].metadata.name}') \
  -- python manage.py refresh_solr chants
```

---

## 11. Verify

```bash
# All pods running
kubectl get pods -n cantus-ultimus
kubectl get pods -n postgres

# App API responds
kubectl exec -n cantus-ultimus \
  $(kubectl get pod -n cantus-ultimus -l app=app -o jsonpath='{.items[0].metadata.name}') \
  -- curl -s http://localhost:8001/manuscripts/ | head -c 200

# Celery worker connected
kubectl logs -n cantus-ultimus deployment/celery --tail=20

# Nginx static files served
curl -I https://cantus.simssa.ca/static/admin/css/base.css

# Folio viewer loads
curl -s "https://cantus.simssa.ca/manifest-proxy/https://www.e-codices.unifr.ch/metadata/iiif/bcj-0018/manifest.json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('@type'))"
```

---

## 12. DNS Cutover

Once the k8s deployment is verified:

1. Update the DNS A record for `cantus.simssa.ca` to point to the k3s node IP.
2. Lower TTL ahead of time (e.g. to 60s) to minimize propagation delay.
3. Monitor error rates for 30 minutes after cutover.
4. Keep the Docker Compose deployment running until DNS has fully propagated.

---

## Rollback

If issues arise after cutover, revert DNS to the old server IP.
The Docker Compose deployment requires no changes to resume serving traffic.