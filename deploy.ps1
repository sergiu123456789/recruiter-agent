# ============================================================
# PowerShell Deployment Script for Recruiter Agent (Cloud Run)
# Project ID: recruiter-agent-12345
# Region: europe-west1
# ============================================================

$PROJECT_ID = "recruiter-agent-12345"
$REGION     = "europe-west1"
$REPO       = "recruiter-agent"
$IMAGE_NAME = "recruiter-agent"
$AR_URL     = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_NAME"

Write-Host "Checking build context..."
Write-Host "Current directory: $(Get-Location)"

if (!(Test-Path "./Dockerfile")) {
    Write-Host "ERROR: Dockerfile not found. Run deploy.ps1 from the project root!"
    exit 1
}

Write-Host "Step 1: Docker clean build..."
docker build --no-cache -t $IMAGE_NAME .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!"
    exit 1
}

Write-Host "Step 2: Tagging image for Artifact Registry..."
docker tag $IMAGE_NAME $AR_URL

Write-Host "Step 3: Authenticating Docker with Artifact Registry..."
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

Write-Host "Step 4: Pushing image to Artifact Registry..."
docker push $AR_URL

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker push failed!"
    exit 1
}

Write-Host "Step 5: Deploying to Cloud Run..."
gcloud run deploy $IMAGE_NAME `
    --image $AR_URL `
    --region $REGION `
    --allow-unauthenticated `
    --timeout=600s `
    --min-instances=1 `
    --set-env-vars GOOGLE_API_KEY=$env:GOOGLE_API_KEY

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed!"
    exit 1
}

Write-Host "Deployment completed successfully!"
Write-Host "Service URL:"

$serviceUrl = gcloud run services describe $IMAGE_NAME --region $REGION --format='value(status.url)'
Write-Host $serviceUrl
