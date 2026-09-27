param(
    [string]$EnvFile = ".env"
)

kubectl create namespace zingsa --dry-run=client -o yaml | kubectl apply -f -
kubectl -n zingsa create secret generic zingsa-env --from-env-file=$EnvFile --dry-run=client -o yaml | kubectl apply -f -

$dbPassword = $null
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { return }
    $parts = $line -split "=", 2
    if ($parts.Length -eq 2 -and $parts[0].Trim() -eq "DJANGO_DB_PASSWORD") {
        $dbPassword = $parts[1].Trim().Trim('"').Trim("'")
    }
}
if ([string]::IsNullOrWhiteSpace($dbPassword)) {
    throw "DJANGO_DB_PASSWORD is required in $EnvFile"
}

# CloudNativePG owner is zingsa_collect. The password matches DJANGO_DB_PASSWORD.
kubectl -n zingsa create secret generic postgis-app `
    --type=kubernetes.io/basic-auth `
    --from-literal=username=zingsa_collect `
    --from-literal=password=$dbPassword `
    --dry-run=client -o yaml | kubectl apply -f -
