# Cloud Run Tailscale Proxy

This proxy service runs on Google Cloud Run and forwards requests to your Mac via Tailscale network.

## Architecture

```
Internet → Cloud Run (Tailscale Proxy) → Tailscale Network → Your Mac (100.84.184.84:8080)
```

## Deployment Steps

### 1. Get Tailscale Auth Key

1. Go to https://login.tailscale.com/admin/settings/keys
2. Generate new auth key:
   - **Reusable**: Yes
   - **Ephemeral**: No
   - **Pre-authorized**: Yes
   - **Tags**: `tag:proxy`
3. Copy the key (starts with `tskey-auth-...`)

### 2. Enable Google Cloud Services

```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
```

### 3. Build and Deploy

From the `cloud_proxy` directory:

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export TAILSCALE_AUTH_KEY="tskey-auth-xxxxx"

# Submit build to Cloud Run
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_TAILSCALE_AUTH_KEY="${TAILSCALE_AUTH_KEY}" \
  --project=${PROJECT_ID}
```

### 4. Get Cloud Run URL

```bash
gcloud run services describe dev-proxy --region=us-central1 --format='value(status.url)'
```

### 5. Map Custom Domain (Optional)

1. In Google Cloud Console → Cloud Run → dev-proxy → "Manage Custom Domains"
2. Add domain: `davidlybeck.com`
3. Add mapping: `davidlybeck.com/dev` → `dev-proxy`
4. Update DNS records as instructed

## Testing

```bash
# Get Cloud Run URL
PROXY_URL=$(gcloud run services describe dev-proxy --region=us-central1 --format='value(status.url)')

# Test health endpoint
curl ${PROXY_URL}/health

# Test proxy to Mac (should show login page)
curl ${PROXY_URL}/dev/login
```

## Monitoring

View logs:
```bash
gcloud run services logs read dev-proxy --region=us-central1 --limit=50
```

## Cost Estimate

- **Cloud Run**: ~$5-10/month (assumes moderate usage)
- **Egress**: Minimal (most data stays on Tailscale)
- **Container Registry**: <$1/month

Total: **~$6-11/month**

## Updating

To update the proxy code:

```bash
gcloud builds submit --config cloudbuild.yaml --project=${PROJECT_ID}
```

The service will automatically use the new version.

## Troubleshooting

**Proxy can't connect to Mac:**
- Verify Mac is running and connected to Tailscale
- Check Mac IP is still `100.84.184.84`: `tailscale ip -4`
- Verify Mac server is running on port 8080

**Tailscale won't connect in Cloud Run:**
- Check auth key is valid and hasn't expired
- Verify auth key is reusable and pre-authorized
- Check Cloud Run logs: `gcloud run services logs read dev-proxy`
