param(
    [string]$EnvFile = ".env"
)

kubectl create namespace zingsa --dry-run=client -o yaml | kubectl apply -f -
kubectl -n zingsa create secret generic zingsa-env --from-env-file=$EnvFile --dry-run=client -o yaml | kubectl apply -f -
