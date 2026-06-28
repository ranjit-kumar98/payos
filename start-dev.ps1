Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting PayOS Development Environment..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Start Docker services
docker compose up -d

Write-Host ""
Write-Host "Waiting 20 seconds for services to start..."
Start-Sleep -Seconds 20

Write-Host ""
Write-Host "Running Containers:"
docker ps

Write-Host ""
Write-Host "Opening PayOS URLs..."

Start-Process "http://localhost:8000/health"
Start-Process "http://localhost:8000/docs#/"
Start-Process "http://localhost:8081/"
Start-Process "http://localhost:8080/"
Start-Process "http://localhost:3000/"
Start-Process "http://localhost/"
Start-Process "http://localhost/api/health"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "PayOS Started Successfully" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green