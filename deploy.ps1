<#
====================================================================================
    Cloud Run Deployment Script (Windows PowerShell)
    Builds Docker image → pushes to Artifact Registry → deploys to Cloud Run
====================================================================================
#>

param(
    [string]$ServiceName = "recruiter-agent",
    [string]$Region      = "europe-west1",
    [string]$Project     = "recruiter-agent-12345"
)

Write-Host "🚀 Starting deployment for $ServiceName ..." -ForegroundColor Cyan

# ---------------------------------------------------------
# Load environment variables from Windows environment
# ---------------------------------------------------------

$GoogleApiKey   = $env:GOOGLE_API_KEY
$GithubUsername = $env:GITHUB_USERNAME
$GithubToken    = $env:GITHUB_TOKEN
$LogLevel       = "INFO"

if (-not $GoogleApiKey) {
    Write-Host "❌ ERROR: GOOGLE_API_KEY is not set in your environment!" -ForegroundColor Red
    Write-Host "Set it with:  setx GOOGLE_API_KEY \"your-key-here\"" -ForegroundColor Yellow
    exit 1
}

if (-not $GithubUsername) {
    $GithubUsername = "sergiu123456789"
}

# ---------------------------------------------------------
# Step 1: Enable required Google APIs
# ---------------------------------------------------------
Write-Host "🔧 Enabling required Google APIs..." -ForegroundColor Cyan

gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# ---------------------------------------------------------
# Step 2: Configure Artifact Registry repo (if not exists)
# ---------------------------------------------------------
Write-Host "📦 Checking Artifact Registry repository..." -ForegroundColor Cyan

$RepoName = "containers"

gcloud artifacts repositories create $RepoName `
    --repository-format=docker `
    --location=$Region `
    --project=$Project `
    --quiet `
    2>$null

# ---------------------------------------------------------
# Step 3: Build Docker image
# ---------------------------------------------------------
Write-Host "🐳 Building Docker image..." -ForegroundColor Cyan

$ImageUri = "europe-west1-docker.pkg.dev/$Project/containers/$ServiceName"

gcloud builds submit `
    --tag $ImageUri `
    --project $Project

# ---------------------------------------------------------
# Step 4: Deploy to Cloud Run
# ---------------------------------------------------------
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

# Prepare argument list
$envVars = @(
    "GOOGLE_API_KEY=$GoogleApiKey",
    "GITHUB_USERNAME=$GithubUsername",
    "SESSION_DB_PATH=/tmp/sessions.db",
    "LOG_LEVEL=$LogLevel"
)

if ($GithubToken) {
    $envVars += "GITHUB_TOKEN=$GithubToken"
}

$envVarsString = [string]::Join(",", $envVars)

gcloud run deploy $ServiceName `
  --image $ImageUri `
  --region $Region `
  --project $Project `
  --allow-unauthenticated `
  --set-env-vars $envVarsString

Write-Host "✅ Deployment complete!" -ForegroundColor Green

$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format="value(status.url)"
Write-Host "🌍 Service URL: $ServiceUrl" -ForegroundColor Cyan
