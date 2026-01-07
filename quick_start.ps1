# Quick Start Script for MedBot
# Run this after Docker containers are up

Write-Host "🏥 MedBot - Quick Start Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "1. Checking Docker status..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Check if containers are up
Write-Host "2. Checking MedBot containers..." -ForegroundColor Yellow
$ollamaContainer = docker ps --filter "name=medbot_ollama" --format "{{.Names}}"
$appContainer = docker ps --filter "name=medbot_streamlit" --format "{{.Names}}"

if (-not $ollamaContainer) {
    Write-Host "⚠️ Ollama container not running. Starting containers..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
}
else {
    Write-Host "✓ Ollama container is running" -ForegroundColor Green
}

if (-not $appContainer) {
    Write-Host "⚠️ MedBot app container not running" -ForegroundColor Yellow
}
else {
    Write-Host "✓ MedBot app container is running" -ForegroundColor Green
}
Write-Host ""

# Check if Mistral model is downloaded
Write-Host "3. Checking Mistral model..." -ForegroundColor Yellow
$modelCheck = docker exec medbot_ollama ollama list 2>$null | Select-String "mistral"

if (-not $modelCheck) {
    Write-Host "⚠️ Mistral model not found. Downloading..." -ForegroundColor Yellow
    Write-Host "   This may take 5-10 minutes..." -ForegroundColor Gray
    docker exec medbot_ollama ollama pull mistral
    Write-Host "✓ Mistral model downloaded" -ForegroundColor Green
}
else {
    Write-Host "✓ Mistral model is available" -ForegroundColor Green
}
Write-Host ""

# Check application health
Write-Host "4. Testing application connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✓ Streamlit app is accessible" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Streamlit app not yet accessible (may still be starting)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Access MedBot at:" -ForegroundColor Cyan
Write-Host "  👉 http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  • View logs:          docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • Restart:            docker-compose restart" -ForegroundColor Gray
Write-Host "  • Stop:               docker-compose down" -ForegroundColor Gray
Write-Host "  • View containers:    docker ps" -ForegroundColor Gray
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:8501"
