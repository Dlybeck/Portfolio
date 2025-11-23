#!/bin/bash
# Quick script to restart Cloud Run service when SOCKS5 connections get stale

echo "🔄 Restarting Cloud Run service to clear stale connections..."

# This forces a new deployment which clears all connection pools
gcloud run deploy portfolio \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --quiet

echo "✅ Cloud Run restarted! Wait 1-2 minutes then try logging in again."
echo "   URL: https://portfolio-q6j7ikwabq-uw.a.run.app/dev/login"
