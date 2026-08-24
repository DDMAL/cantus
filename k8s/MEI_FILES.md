# The MEI files volume

`index_manuscript_mei` reads MEI from a directory on disk. The
`production-mei-files` submodule is `COPY`'d into the app image
(`app/Dockerfile`), so anything written next to it inside a running container is
lost on the next deploy. Published MEI deposits therefore live on a persistent
volume instead, mounted at `/code/mei-files` in both the `app` and `celery`
pods and named by `MEI_FILES_DIR`.

| | production | staging |
|---|---|---|
| PV / PVC | `mei-files-pv` / `mei-files-pvc` | `mei-files-staging-pv` / `mei-files-staging-pvc` |
| NFS path | `/srv/nfs/cantus/mei_files` | `/srv/nfs/cantus-staging/mei_files` |

Both environments live in the `cantus-ultimus` namespace, so staging objects
carry the `-staging` suffix. **The volumes are separate on purpose:** publishing
writes files and `index_manuscript_mei --replace` deletes index entries, so a
shared volume would let staging destroy production MEI.

`ReadWriteMany` is required rather than incidental — `app` and `celery` are
separate pods, and celery writes and indexes while app serves the admin's
download link.

## Server preparation (192.168.236.171)

Create **and export** each path before any pod starts:

```bash
mkdir -p /srv/nfs/cantus/mei_files
# add to /etc/exports, then:
exportfs -ra
```

Two failure modes to know about:

- A static PV binds `Bound` whether or not the export exists. A missing or
  unexported path only shows up at pod start, as
  `mount.nfs4: ... No such file or directory` with the pod stuck in
  `ContainerCreating`. The path must also sit inside the NFSv4 pseudo-root.
- The app image declares no `USER`, so containers run as root. Under the default
  `root_squash` the pod's root maps to `nobody` and **writes fail** — which
  surfaces as a failed publish task rather than as a mount error, long after
  deployment looks healthy. The export needs `no_root_squash`, matching
  `/srv/nfs/mothra/stored_models` on the other storage VM, which is why Mothra's
  root-running pods can write to a `drwxrwx--- 999 999` directory:

  ```
  /srv/nfs/cantus/mei_files <cluster-cidr>(rw,sync,no_subtree_check,no_root_squash)
  ```

  If you would rather keep `root_squash`, give the directory to the export's
  anonymous identity instead (`chown -R 65534:65534`, or `chmod 0777`).

  Either way, check it directly after deploying — this is the failure mode most
  likely to be discovered late:

  ```bash
  kubectl exec deploy/celery -n cantus-ultimus -- touch /code/mei-files/.wtest
  ```

## Applying

CI only runs `kubectl set image` (`.github/workflows/build_push_deploy.yml`); it
never applies manifests. Editing the YAML in this repo does nothing on its own:

```bash
kubectl apply -f k8s/cantus-ultimus/mei-files-pv.yaml
kubectl apply -f k8s/cantus-ultimus/mei-files-pvc.yaml
kubectl apply -f k8s/cantus-ultimus/app/configmap.yaml
kubectl apply -f k8s/cantus-ultimus/app/deployment.yaml
kubectl apply -f k8s/cantus-ultimus/celery/deployment.yaml
```

**Name the files, never the directory.** `kubectl apply -f
k8s/cantus-ultimus/app/` also applies `secret.yaml`, whose `stringData` holds
the literal string `<value>` for `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, and
`RABBIT_PASSWORD` -- the repo copy is a template, and the real values live only
in the cluster. Applying it overwrites the live `app-secret` with placeholders,
which does not fail and does not restart anything: the site keeps running on the
env vars its current pods already read, and loses the database and the broker at
the next pod restart, whenever that happens to be.

Apply these **before** the merge that deploys the code. Both Deployments pin
`image: ghcr.io/ddmal/cantus-app:main-latest`, so applying them while production
runs the current `main` rolls the volume mount in without changing the code;
applying them after CI has run `kubectl set image` would drag the image back to
whatever `main-latest` points at. Getting the mount in first also matters because
`MEI_FILES_DIR` defaults to `/code/mei-files` whether or not anything is mounted
there -- new code on an unmounted pod publishes into the container's own
filesystem, reporting success and losing the file at the next restart.

Check that the mount really is the NFS export, and that root can write to it
-- under the default `root_squash` the mount succeeds and only the writes fail,
which surfaces much later as a failed publish task rather than as a mount error:

```bash
kubectl exec deploy/celery -n cantus-ultimus -- mount | grep mei-files
kubectl exec deploy/celery -n cantus-ultimus -- touch /code/mei-files/.wtest
kubectl exec deploy/celery -n cantus-ultimus -- ls -l /code/mei-files/.wtest
```

The test file must come back owned by `root`, not `nobody`.

Migrations come *after* the code deploy, not here: `0007_meisubmission` ships
with the new image, so there is nothing to apply until CI has rolled it out.
Once it has:

```bash
kubectl exec deploy/app -n cantus-ultimus -- python manage.py migrate
```

## Seeding

Copy each manuscript's curated MEI into the volume once, so the volume holds
*every* folio of the manuscript rather than only the deposited ones:

```bash
kubectl exec deploy/app -n cantus-ultimus -- \
  python manage.py seed_mei_files <manuscript_id>
```

This matters because `index_manuscript_mei` takes a single `--mei-dir`: a
whole-manuscript reindex pointed at a volume holding only deposits would drop
every folio that came from the curated archive. Re-run it (with `--overwrite`
when you mean to discard published deposits) after the submodule is updated
upstream.

## Recovery

The submitted MEI is stored in Postgres, so the volume is reconstructable:

```bash
kubectl exec deploy/app -n cantus-ultimus -- \
  python manage.py reindex_published_submissions <manuscript_id>
```

That restores any missing published file from the database and reindexes it. Use
it after a Solr rebuild, or if the volume is ever restored from a backup older
than the database.
