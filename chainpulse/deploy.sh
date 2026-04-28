#!/bin/bash
set -e

echo "═══════════════════════════════════════"
echo "  ChainPulse — Deployment Script"
echo "═══════════════════════════════════════"

# Check required vars
if [ -z "$GEMINI_API_KEY" ]; then echo "ERROR: Set GEMINI_API_KEY"; exit 1; fi
if [ -z "$PROJECT_ID" ]; then echo "ERROR: Set PROJECT_ID"; exit 1; fi

# ── 1. Backend → Google Cloud Run ──────────────────────
echo ""
echo "▸ Deploying backend to Cloud Run..."
cd backend

gcloud builds submit --tag gcr.io/$PROJECT_ID/chainpulse-backend

gcloud run deploy chainpulse-backend \
  --image gcr.io/$PROJECT_ID/chainpulse-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --port 8080 \
  --min-instances 1 \
  --max-instances 3 \
  --memory 512Mi

BACKEND_URL=$(gcloud run services describe chainpulse-backend \
  --platform managed --region us-central1 \
  --format 'value(status.url)')

echo "✅ Backend deployed: $BACKEND_URL"
cd ..

# ── 2. Frontend → Firebase Hosting ────────────────────
echo ""
echo "▸ Updating frontend BACKEND_URL..."

# Inject backend URL into index.html
sed -i "s|window.BACKEND_URL || 'http://localhost:8080'|'$BACKEND_URL'|g" frontend/index.html

echo "▸ Deploying frontend to Firebase Hosting..."
firebase init hosting --project $PROJECT_ID <<EOF
frontend
index.html
n
EOF

firebase deploy --only hosting --project $PROJECT_ID

echo ""
echo "═══════════════════════════════════════"
echo "  ✅ Deployment Complete!"
echo "  Backend:  $BACKEND_URL"
echo "  API Docs: $BACKEND_URL/docs"
echo "═══════════════════════════════════════"
