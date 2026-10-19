# ZINGSA Collect on k3s

Collect runs on the same single-node k3s cluster as NSDI (`zingsa-hpdesktop460p2xx`, LAN `172.16.3.24`, public `41.174.184.62`), in its own namespace `zingsa`. GitHub-hosted runners cannot reach the control plane, so deploys run on a self-hosted runner on that node. The kubeconfig on the node is `/etc/rancher/k3s/k3s.yaml`.

Pods set `nodeSelector` `kubernetes.io/hostname` so they run where the imported images are. Manifests ship with `REPLACE_WITH_NODE_HOSTNAME`. `scripts/k8s-deploy-remote.sh` reads the live name with `kubectl get nodes` and substitutes it before `kubectl apply -k`. For a manual apply, substitute it first:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
NODE="$(kubectl get nodes -l node-role.kubernetes.io/control-plane -o jsonpath='{.items[0].metadata.name}')"
grep -R -l REPLACE_WITH_NODE_HOSTNAME k8s/*.yaml | while read -r file; do
  sed -i "s/REPLACE_WITH_NODE_HOSTNAME/${NODE}/g" "$file"
done
```

Public access is NodePort. There is no Ingress.

## Shared with NSDI

- The CloudNativePG operator in `cnpg-system` (1.26.1) is shared. This bundle does **not** install or upgrade it; NSDI's database depends on it. The deploy script stops if its CRDs are missing.
- NodePorts must not collide. NSDI uses 30105, 30432, and 30951.
- This host cannot pull images reliably. k3s already caches `redis:7-alpine` and `ghcr.io/cloudnative-pg/postgis:16`. The deploy script copies `minio/minio:latest` and `minio/mc:latest` from the host Docker cache into k3s containerd.

## First deploy, in order

1. **Frontend build.** `ux_ui/` is committed because the image is built from this repo. In `zc_frontend`, run `pnpm build:ux`, then commit `ux_ui/` here. The export calls `/api` on the same origin.

2. **Runner.** On the control plane, create a registration token for `blezzed/zingsa_collect` (Settings → Actions → Runners → New self-hosted runner) and run:

   ```bash
   export RUNNER_TOKEN=...   # registration token, never committed
   bash scripts/install-github-runner.sh
   ```

   It registers with the label `zingsa-collect-k3s`, which the workflow requires. NSDI's runner is registered to `nsdi_backend` and cannot run these jobs.

3. **Secrets.** On the control plane, reuse the Docker `.env`. The ConfigMap overrides its host, port, and URL keys:

   ```bash
   bash k8s/create-secret.sh /home/zingsa/Documents/zingsa_collect/.env
   ```

   This creates `zingsa-env` from the env file, plus the CloudNativePG secret `postgis-app` (`username=zingsa_collect`, password from `DJANGO_DB_PASSWORD`). The file must contain `DJANGO_SECRET_KEY`, `DJANGO_DB_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `MAINTENANCE_OWNER_TOKEN`. `k8s/secret.example.yaml` lists the keys. From a machine with cluster access, `pwsh k8s/create-secret.ps1 -EnvFile .env` does the same.

4. **Deploy.** Push to `main`, or dispatch the workflow with `deploy`. The cluster starts with an empty database; the Docker stack keeps serving `:8206` meanwhile.

5. **Move the data.** On the control plane:

   ```bash
   export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
   bash scripts/migrate-docker-to-k3s.sh preflight   # read-only
   bash scripts/migrate-docker-to-k3s.sh db          # downtime starts: Docker app stops
   bash scripts/migrate-docker-to-k3s.sh media       # MinIO bucket mirror
   bash scripts/migrate-docker-to-k3s.sh cutover     # k3s app starts, smoke test
   ```

   `db` compares exact row counts for every table between Docker and k3s and stops if any differ. `rollback` scales the k3s app to 0 and restarts the Docker app. Docker PostGIS and MinIO are never modified.

6. **Clients.** Move mobile apps and bookmarks from `:8206` to `:30206`. For public access, the router must forward `41.174.184.62:30206`. When k3s has been stable, run `docker compose down` in `/home/zingsa/Documents/zingsa_collect`.

## Workflow

`.github/workflows/deploy-k8s.yml` ("Build and deploy") runs on `[self-hosted, linux, zingsa-collect-k3s]`.

| Action | What it does |
| --- | --- |
| `deploy` (push to `main` or `master`, or the default dispatch) | Build `blezzed/zingsa-collect` on the node, import it into k3s containerd, apply `k8s/`, roll web, worker, and beat |
| `apply-config` | Apply `k8s/01-configmap.yaml`, restart web, worker, and beat, print the live public URL keys |
| `maintenance` | Set `MAINTENANCE_MODE=1` on web, worker, and beat. Public HTTP returns 503. The owner bypass still works. No image rebuild |
| `maintenance-off` | Set `MAINTENANCE_MODE=0` and wait for rollouts |
| `stop` | Scale web, worker, and beat to 0. PostGIS, Redis, and MinIO keep running |
| `start` | Scale web, worker, and beat back to 1 and wait |

Push ignores docs, markdown, PDFs, the SQL dump, form JSON, and the seed scripts.

Optional GitHub secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` (only if an image is also pulled or pushed), `SLACK_WEBHOOK_URL`. `MAINTENANCE_OWNER_TOKEN` lives in the Kubernetes Secret, not GitHub.

## Database

Postgres is a CloudNativePG `Cluster` named `postgis` with one instance, 20Gi on `local-path`, the same shape as NSDI. Django uses the primary Service `postgis-rw:5432`. The ConfigMap sets `DJANGO_DB_HOST`, so the Docker `.env` value never applies. Web and worker read the database user and password from `postgis-app`.

Web runs `migrate` and `collectstatic` on startup, then Daphne on `0.0.0.0:8005`. WhiteNoise serves `/static/`. Uploads go to MinIO.

## NodePorts

| Service | Cluster DNS | NodePort | Who should reach it |
| --- | --- | --- | --- |
| web | `web:8005` | **30206** | Public. App, admin, API, and media via `/minio/` |
| postgis primary | `postgis-rw:5432` | **30433** (`postgis-nodeport`) | Admins only. Firewall this port |
| minio API | `minio:9000` | **30918** | Admins and the migration script. Browsers use `/minio/` on 30206 |
| minio console | `minio:9001` | **30919** | Admins only. Firewall this port |
| redis | `redis:6379` | none | Cluster only |

App URLs: `http://172.16.3.24:30206` (LAN) and `http://41.174.184.62:30206` (public).

Edit `k8s/01-configmap.yaml` if an address changes, then:

```bash
KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash scripts/apply-public-urls.sh
```

## Check the cluster

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl -n zingsa get pods,svc
kubectl -n zingsa get cluster
kubectl -n zingsa logs deploy/web
kubectl -n zingsa logs deploy/worker
kubectl -n zingsa logs deploy/beat
```

## Maintenance

```bash
KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash scripts/k8s-ops.sh maintenance
KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash scripts/k8s-ops.sh maintenance-off
```

Or dispatch the workflow with `maintenance` or `maintenance-off`. Neither rebuilds the image.

While maintenance is on, everyone else gets HTTP 503 and `Retry-After: 300`. API clients get `{"detail":"maintenance","message":"..."}`. Browsers get `templates/maintenance.html`.

The owner bypass still works:

- `POST /__owner/maintenance-bypass/` with form field `token` (GET with `?token=` also works). That sets the httponly cookie `zingsa_collect_maintenance_bypass`.
- Or send header `X-Maintenance-Owner-Token`.

`POST /__owner/maintenance-bypass/clear/` removes the cookie.

Beat stays at 1 replica. `stop` does not scale Redis, MinIO, or PostGIS.
