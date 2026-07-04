#!/usr/bin/env bash
# Lipi → GCP full deploy script
# Deploys: Lipi app + Medical Data Toolkit to Cloud Run (asia-south1)
# Database: Cloud SQL PostgreSQL (db-f1-micro, free trial)
# Run: bash deploy-gcp.sh
set -euo pipefail

# ─── CONFIG — fill these before running ───────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-}"          # e.g. lipi-prod-123456
REGION="asia-south1"                      # Mumbai
LIPI_SERVICE="lipi"
MDT_SERVICE="lipi-mdt"
REGISTRY="${REGION}-docker.pkg.dev"
REPO="lipi-repo"
SQL_INSTANCE="lipi-db"
SQL_DB="lipi"
SQL_USER="lipi"

# Secrets — passed via env or prompted below
SECRET_KEY="${SECRET_KEY:-}"
SARVAM_API_KEY="${SARVAM_API_KEY:-}"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
SHRUTI_ADMIN_PASSWORD="${SHRUTI_ADMIN_PASSWORD:-}"
SQL_PASSWORD="${SQL_PASSWORD:-}"

# ─── PROMPT for missing values ─────────────────────────────────────────────────
if [ -z "$PROJECT_ID" ]; then
  echo ""
  gcloud projects list --format="table(projectId,name)" 2>/dev/null || true
  read -rp $'\nEnter your GCP Project ID: ' PROJECT_ID
fi

prompt_secret() {
  local var_name="$1" prompt_text="$2"
  if [ -z "${!var_name}" ]; then
    read -rsp "$prompt_text: " val; echo ""
    eval "$var_name='$val'"
  fi
}

prompt_secret SECRET_KEY        "JWT SECRET_KEY (random string, e.g. openssl rand -hex 32)"
prompt_secret SARVAM_API_KEY    "SARVAM_API_KEY"
prompt_secret GEMINI_API_KEY    "GEMINI_API_KEY"
prompt_secret SHRUTI_ADMIN_PASSWORD "SHRUTI_ADMIN_PASSWORD (demo admin login)"
prompt_secret SQL_PASSWORD      "Cloud SQL password for user 'lipi' (pick any strong password)"

IMAGE_LIPI="${REGISTRY}/${PROJECT_ID}/${REPO}/${LIPI_SERVICE}:latest"
IMAGE_MDT="${REGISTRY}/${PROJECT_ID}/${REPO}/${MDT_SERVICE}:latest"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Project : $PROJECT_ID"
echo "  Region  : $REGION"
echo "  Lipi    : $IMAGE_LIPI"
echo "  MDT     : $IMAGE_MDT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

gcloud config set project "$PROJECT_ID"

# ─── 1. Enable APIs ────────────────────────────────────────────────────────────
echo "▶ Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project="$PROJECT_ID"

# ─── 2. Artifact Registry ──────────────────────────────────────────────────────
echo "▶ Creating Artifact Registry repository..."
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT_ID" 2>/dev/null || echo "  (repo already exists)"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ─── 3. Cloud SQL ──────────────────────────────────────────────────────────────
echo "▶ Creating Cloud SQL instance (this takes ~5 min on first run)..."
if ! gcloud sql instances describe "$SQL_INSTANCE" --project="$PROJECT_ID" &>/dev/null; then
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --storage-size=10GB \
    --storage-auto-increase \
    --project="$PROJECT_ID"
fi

echo "▶ Creating database and user..."
gcloud sql databases create "$SQL_DB" \
  --instance="$SQL_INSTANCE" \
  --project="$PROJECT_ID" 2>/dev/null || echo "  (db already exists)"

gcloud sql users create "$SQL_USER" \
  --instance="$SQL_INSTANCE" \
  --password="$SQL_PASSWORD" \
  --project="$PROJECT_ID" 2>/dev/null || \
  gcloud sql users set-password "$SQL_USER" \
    --instance="$SQL_INSTANCE" \
    --password="$SQL_PASSWORD" \
    --project="$PROJECT_ID"

SQL_CONN_NAME=$(gcloud sql instances describe "$SQL_INSTANCE" \
  --project="$PROJECT_ID" \
  --format="value(connectionName)")
DATABASE_URL="postgresql://${SQL_USER}:${SQL_PASSWORD}@/${SQL_DB}?host=/cloudsql/${SQL_CONN_NAME}"

echo "  SQL connection: $SQL_CONN_NAME"

# ─── 4. Grant Cloud SQL Client role to the default Cloud Run service account ──
echo "▶ Granting Cloud SQL Client role to Cloud Run service account..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA}" \
  --role="roles/cloudsql.client" \
  --condition=None \
  --quiet 2>/dev/null || true

# ─── 5. Build and push Lipi image ─────────────────────────────────────────────
echo "▶ Building Lipi Docker image..."
docker build \
  --platform linux/amd64 \
  -t "$IMAGE_LIPI" \
  -f Dockerfile \
  .

echo "▶ Pushing Lipi image..."
docker push "$IMAGE_LIPI"

# ─── 6. Build Medical Data Toolkit for linux/amd64 and push ──────────────────
echo "▶ Building Medical Data Toolkit for linux/amd64 (cross-compile)..."
docker buildx build \
  --platform linux/amd64 \
  -t "$IMAGE_MDT" \
  vendor/medical-data-toolkit/ \
  --push

# ─── 6. Deploy Medical Data Toolkit ──────────────────────────────────────────
echo "▶ Deploying Medical Data Toolkit to Cloud Run..."
gcloud run deploy "$MDT_SERVICE" \
  --image="$IMAGE_MDT" \
  --platform=managed \
  --region="$REGION" \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=3 \
  --port=8080 \
  --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --project="$PROJECT_ID"

MDT_URL=$(gcloud run services describe "$MDT_SERVICE" \
  --platform=managed \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

echo "  MDT live at: $MDT_URL"

# ─── 7. Deploy Lipi app ────────────────────────────────────────────────────────
echo "▶ Deploying Lipi app to Cloud Run..."

# Lipi URL isn't known before deploy, so we deploy once then update CORS
gcloud run deploy "$LIPI_SERVICE" \
  --image="$IMAGE_LIPI" \
  --platform=managed \
  --region="$REGION" \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --port=8000 \
  --add-cloudsql-instances="$SQL_CONN_NAME" \
  --set-env-vars="\
DATABASE_URL=${DATABASE_URL},\
SECRET_KEY=${SECRET_KEY},\
SARVAM_API_KEY=${SARVAM_API_KEY},\
GEMINI_API_KEY=${GEMINI_API_KEY},\
SHRUTI_ADMIN_USER=demo,\
SHRUTI_ADMIN_PASSWORD=${SHRUTI_ADMIN_PASSWORD},\
SEED_DEMO_USER=true,\
DEMO_USERNAME=demo,\
DEMO_FULL_NAME=Dr. Demo,\
ASR_MODE=cloud,\
MEDICAL_DATA_TOOLKIT_URL=${MDT_URL},\
APP_BASE_URL=PLACEHOLDER,\
CORS_ORIGINS=PLACEHOLDER,\
POSTGRES_POOL_MIN_SIZE=1,\
POSTGRES_POOL_MAX_SIZE=5" \
  --project="$PROJECT_ID"

LIPI_URL=$(gcloud run services describe "$LIPI_SERVICE" \
  --platform=managed \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

echo "  Lipi live at: $LIPI_URL"

# ─── 8. Update CORS and APP_BASE_URL with real URL ────────────────────────────
echo "▶ Updating CORS and APP_BASE_URL with real URL..."
gcloud run services update "$LIPI_SERVICE" \
  --platform=managed \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --update-env-vars="\
APP_BASE_URL=${LIPI_URL},\
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,${LIPI_URL}"

# ─── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ DEPLOY COMPLETE"
echo ""
echo "  Lipi app   : ${LIPI_URL}"
echo "  MDT        : ${MDT_URL}"
echo "  Health     : ${LIPI_URL}/api/health"
echo ""
echo "  Demo login : demo / (your SHRUTI_ADMIN_PASSWORD)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Next: test ${LIPI_URL}/api/health, then login."
echo "  If you have a custom domain, run: gcloud run domain-mappings create"
