#!/bin/bash
echo "🚀 Deploying to Google Cloud Run..."

gcloud run deploy vibetrace-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080

echo "✅ Deployment Complete!"
