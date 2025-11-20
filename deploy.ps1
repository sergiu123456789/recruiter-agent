# PowerShell deployment script for Cloud Run (Windows-safe)
param(
    [string]$ServiceName = "recruiter-agent",
    [string]$Region = "europe-west1"
)

Write-Host "🚀 Deploying $ServiceName to Cloud Run..."

gcloud run deploy $ServiceName `
  --source . `
  --region $Region `
  --allow-unauthenticated

Write-Host "✅ Deployment complete."
