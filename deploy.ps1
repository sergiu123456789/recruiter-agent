# ============================================================
# Recruiter Agent Deployment Script (PowerShell 5.1 SAFE)
# ============================================================

$PROJECT_ID = "recruiter-agent-12345"
$REGION     = "europe-west1"
$REPO       = "recruiter-agent"
$IMAGE_NAME = "recruiter-agent"
$AR_URL     = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_NAME"

Write-Host "Working directory: $(Get-Location)"

# Validate build context
if (!(Test-Path "./Dockerfile")) {
    Write-Host "ERROR: Dockerfile not found!"
    exit 1
}
if (!(Test-Path "./app/cv.txt")) {
    Write-Host "ERROR: app/cv.txt missing!"
    exit 1
}

Write-Host "Build context OK"

# Docker build
Write-Host "Building Docker image..."
docker build -t $IMAGE_NAME .
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Docker build failed."; exit 1 }

# Push image
docker tag $IMAGE_NAME $AR_URL
docker push $AR_URL
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Docker push failed."; exit 1 }

# Cloud Run deploy (NO SPLATTING, NO BACKTICKS)
Write-Host "Deploying to Cloud Run..."

gcloud run deploy $IMAGE_NAME `
    --image="$AR_URL" `
    --region="$REGION" `
    --platform="managed" `
    --allow-unauthenticated `
    --min-instances=1 `
    --timeout=600s `
    --set-env-vars="GOOGLE_API_KEY=$env:GOOGLE_API_KEY"

if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Deployment failed."; exit 1 }

Write-Host "Deployment complete"
gcloud run services describe $IMAGE_NAME --region $REGION --format="value(status.url)"
