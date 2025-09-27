```bash
kubectl create secret docker-registry ghcr-creds \
  --docker-server=ghcr.io \
  --docker-username=<your-github-username> \
  --docker-password=<your-personal-access-token> \
  --namespace=syncly


kubectl create secret generic syncly-env-mascot \
    --from-literal=API_KEY=your-api-key \
    --from-literal=ENDPOINT=https://api.example.com \
    --from-literal=DB_USER=your-db-user \
    --from-literal=DB_PASS=your-db-pass \
    --from-literal=EXTRA_CONFIG=some-value \
    --namespace=syncly


kubectl create secret generic syncly-env-mascot \
    --from-literal=API_KEY=your-api-key \
    --from-literal=ENDPOINT=https://api.example.com \
    --from-literal=DB_USER=your-db-user \
    --from-literal=DB_PASS=your-db-pass \
    --from-literal=EXTRA_CONFIG=some-value \
    --namespace=syncly

```
