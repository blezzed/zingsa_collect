# ZINGSA Collect on k3s

Single-node k3s. GitHub-hosted runners cannot reach the private control plane, so the deploy job runs on a self-hosted runner on that node. The kubeconfig on the node is `/etc/rancher/k3s/k3s.yaml`.

Every pod sets `nodeSelector` `kubernetes.io/hostname` to the control-plane node. On a single node that pins work to the machine that has the imported image and the local volumes. Manifests ship with `REPLACE_WITH_NODE_HOSTNAME`. This environment cannot reach the cluster. `scripts/k8s-deploy-remote.sh` reads the live name with `kubectl get nodes` and substitutes it before `kubectl apply -k`. For a manual apply, set the hostname first:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes
NODE="$(kubectl get nodes -l node-role.kubernetes.io/control-plane -o jsonpath='{.items[0].metadata.name}')"
grep -R -l REPLACE_WITH_NODE_HOSTNAME k8s/*.yaml | while read -r file; do
  sed -i "s/REPLACE_WITH_NODE_HOSTNAME/${NODE}/g" "$file"
done
```

Public access is NodePort. There is no Ingress in the bundle that `kubectl apply -k k8s` applies.

## Runner

On the control plane, create a registration token for `blezzed/zingsa_collect` and run:

```bash
export RUNNER_TOKEN=...   # registration token, not a personal access token committed to git
bash scripts/install-github-runner.sh
```

Defaults: repository `https://github.com/blezzed/zingsa_collect`, runner name = the control-plane hostname, extra label `zingsa-collect-k3s`. The label `nsdi-k3s` belongs to another app and is not reused. The install directory is `/opt/actions-runner-zingsa-collect` when passwordless sudo works, otherwise `$HOME/actions-runner-zingsa-collect`. Passwordless sudo installs and starts the service. Without it, the script starts `./run.sh` and adds a crontab `@reboot` line.

The runner user must be able to read `/etc/rancher/k3s/k3s.yaml` and use Docker. Installing the service with sudo is the straightforward way to get that access.

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

Push ignores docs, markdown, PDFs, the SQL dump, form JSON, and the seed scripts. Those are not part of the running app.

Optional GitHub secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` (only if an image is also pulled or pushed), `SLACK_WEBHOOK_URL`. There is no `K3S_SSH_KEY`. The runner is already on the control plane.

`MAINTENANCE_OWNER_TOKEN` is not a GitHub secret in this workflow. It lives in the Kubernetes Secret.

## Secret, then apply

Put real values in an env file that is not committed. `k8s/secret.example.yaml` lists the keys. `MAINTENANCE_OWNER_TOKEN` and `MAINTENANCE_MODE` belong in that Secret. The ConfigMap wins when the same key exists in both, so non-secret config such as `DJANGO_DB_HOST` stays on the in-cluster Service even if the env file still has a laptop host.

```powershell
pwsh k8s/create-secret.ps1 -EnvFile .env
```

That runs:

```powershell
kubectl create namespace zingsa --dry-run=client -o yaml | kubectl apply -f -
kubectl -n zingsa create secret generic zingsa-env --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
```

Then, on the control plane, after the hostname substitution above:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl apply -k k8s
```

The app image is not pulled from Docker Hub by the cluster. Build it on the node (or let the workflow build it) and import it. `imagePullPolicy` is `IfNotPresent`. PostGIS, Redis, and MinIO are public images; import them the same way if the node cannot pull from a registry.

Web runs `migrate` and `collectstatic` on startup, then Daphne on `0.0.0.0:8005`. Uploads go to MinIO. The media volume is still mounted at Django's `MEDIA_ROOT` (`/app/config/media`) on web and worker for filesystem storage.

## NodePorts

| Service | Cluster DNS | NodePort | Who should reach it |
| --- | --- | --- | --- |
| web | `web:8005` | **30206** | Public. App and admin. Not 30105 |
| postgis | `postgis:5432` | **30433** | Admins only. Firewall this port. Not 30432 |
| minio API | `minio:9000` | **30918** | Public, so clients can open uploaded files |
| minio console | `minio:9001` | **30919** | Admins only. Firewall this port |
| redis | `redis:6379` | none | Cluster only |

Published app URL, using the LAN address already used by this project:

`http://172.30.5.24:30206`

Edit `k8s/01-configmap.yaml` if the public IP or a separate frontend host is different, then:

```bash
KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash scripts/apply-public-urls.sh
```

## Check the cluster

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl -n zingsa get pods,svc
kubectl -n zingsa logs deploy/web
kubectl -n zingsa logs deploy/worker
kubectl -n zingsa logs deploy/beat
```

## Maintenance

```bash
KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash scripts/k8s-ops.sh maintenance
KUBECONFIG=/etc/rancher/k3s/k3s.yaml bash scripts/k8s-ops.sh maintenance-off
```

Or dispatch the workflow with action `maintenance` or `maintenance-off`. Neither rebuilds the image.

While maintenance is on, everyone else gets HTTP 503 and `Retry-After: 300`. API clients get `{"detail":"maintenance","message":"..."}`. Browsers get `templates/maintenance.html`.

The owner bypass still works:

- `POST /__owner/maintenance-bypass/` with form field `token` (GET with `?token=` also works). That sets the httponly cookie `zingsa_collect_maintenance_bypass`.
- Or send header `X-Maintenance-Owner-Token`.

`POST /__owner/maintenance-bypass/clear/` removes the cookie.

Beat stays at 1 replica. `stop` does not scale Redis, PostGIS, or MinIO.
