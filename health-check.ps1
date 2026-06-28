Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "       PayOS Health Check"
Write-Host "======================================" -ForegroundColor Cyan

# Check Docker Containers
Write-Host ""
Write-Host "Docker Containers"

docker ps --format "table {{.Names}}\t{{.Status}}"

# Backend Health
try {
    $response = Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
    Write-Host "Backend Health          ✅" -ForegroundColor Green
}
catch {
    Write-Host "Backend Health          ❌" -ForegroundColor Red
}

# Swagger
try {
    Invoke-WebRequest http://localhost:8000/docs -UseBasicParsing | Out-Null
    Write-Host "Swagger                ✅" -ForegroundColor Green
}
catch {
    Write-Host "Swagger                ❌" -ForegroundColor Red
}

# Frontend
try {
    Invoke-WebRequest http://localhost:3000 -UseBasicParsing | Out-Null
    Write-Host "Frontend               ✅" -ForegroundColor Green
}
catch {
    Write-Host "Frontend               ❌" -ForegroundColor Red
}

# Nginx
try {
    Invoke-WebRequest http://localhost -UseBasicParsing | Out-Null
    Write-Host "Nginx                  ✅" -ForegroundColor Green
}
catch {
    Write-Host "Nginx                  ❌" -ForegroundColor Red
}

# Backend through Nginx
try {
    Invoke-WebRequest http://localhost/api/health -UseBasicParsing | Out-Null
    Write-Host "Backend via Nginx      ✅" -ForegroundColor Green
}
catch {
    Write-Host "Backend via Nginx      ❌" -ForegroundColor Red
}

# Redis Commander
try {
    Invoke-WebRequest http://localhost:8081 -UseBasicParsing | Out-Null
    Write-Host "Redis Commander        ✅" -ForegroundColor Green
}
catch {
    Write-Host "Redis Commander        ❌" -ForegroundColor Red
}

# Kafka UI
try {
    Invoke-WebRequest http://localhost:8080 -UseBasicParsing | Out-Null
    Write-Host "Kafka UI               ✅" -ForegroundColor Green
}
catch {
    Write-Host "Kafka UI               ❌" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Health Check Finished"
Write-Host "======================================" -ForegroundColor Cyan