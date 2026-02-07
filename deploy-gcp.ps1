# Deploy Code Sandbox Service to GCP Cloud Run
# ==============================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "zenith-486712",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

$ServiceName = "code-sandbox"
$Port = 8003

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deploying $ServiceName" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Build and tag Docker image
Write-Host "Step 1: Building Docker image..." -ForegroundColor Cyan
$ImageName = "gcr.io/$ProjectId/$ServiceName"

docker build -t $ServiceName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed" -ForegroundColor Red
    exit 1
}

docker tag $ServiceName $ImageName
Write-Host "✓ Image built: $ImageName" -ForegroundColor Green
Write-Host ""

# Configure Docker for GCR
Write-Host "Step 2: Configuring Docker for GCR..." -ForegroundColor Cyan
gcloud auth configure-docker
Write-Host ""

# Push to GCR
Write-Host "Step 3: Pushing to Google Container Registry..." -ForegroundColor Cyan
docker push $ImageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker push failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Image pushed to GCR" -ForegroundColor Green
Write-Host ""

# Deploy to Cloud Run
Write-Host "Step 4: Deploying to Cloud Run..." -ForegroundColor Cyan
Write-Host "⚠️  Note: Docker-in-Docker not supported on Cloud Run" -ForegroundColor Yellow
Write-Host "    Code execution will use Python exec() instead" -ForegroundColor Yellow
Write-Host ""

gcloud run deploy $ServiceName `
    --image=$ImageName `
    --platform=managed `
    --region=$Region `
    --port=$Port `
    --memory=2Gi `
    --cpu=2 `
    --timeout=300 `
    --max-instances=10 `
    --allow-unauthenticated `
    --set-env-vars="PORT=$Port" `
    --project=$ProjectId

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cloud Run deployment failed" -ForegroundColor Red
    exit 1
}

# Get service URL
$ServiceUrl = gcloud run services describe $ServiceName --platform=managed --region=$Region --format="value(status.url)" --project=$ProjectId

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Yellow
Write-Host "Health Check: $ServiceUrl/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "View logs:" -ForegroundColor Cyan
Write-Host "  gcloud run logs read --service=$ServiceName --region=$Region --project=$ProjectId" -ForegroundColor White
