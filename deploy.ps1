$ErrorActionPreference = "Stop"

$project = "recruiter-agent-12345"
$region = "europe-west1"

gcloud config set project $project

gcloud builds submit --config cloudbuild.yaml .
