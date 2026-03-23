# Script de subida automática a AWS ECR (Hospital Clinic)
# Este script asume que Docker y AWS CLI están instalados en la máquina que lo ejecuta.

$REGION = "eu-west-1"
$REGISTRY = "248189917711.dkr.ecr.eu-west-1.amazonaws.com"
$REPO = "direccioserveisgenerals/compres/hcb-dsg"
$VERSION = "1.0"

Write-Host "1. Autenticándose en AWS ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $REGISTRY

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en la autenticación con AWS ECR." -ForegroundColor Red
    exit 1
}

Write-Host "2. Construyendo la imagen Docker..." -ForegroundColor Cyan
# Se sube el contexto de todo el proyecto
docker build -t ${REPO}:${VERSION} -f docker/Dockerfile .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error construyendo la imagen Docker." -ForegroundColor Red
    exit 1
}

Write-Host "3. Etiquetando la imagen (Version $VERSION y Latest)..." -ForegroundColor Cyan
docker tag ${REPO}:${VERSION} ${REGISTRY}/${REPO}:${VERSION}
docker tag ${REPO}:${VERSION} ${REGISTRY}/${REPO}:latest

Write-Host "4. Subiendo la imagen al registro ECR del Clinic..." -ForegroundColor Cyan
docker push ${REGISTRY}/${REPO}:${VERSION}
docker push ${REGISTRY}/${REPO}:latest

Write-Host "✅ ¡Proceso completado con éxito! La imagen ya está en AWS ECR." -ForegroundColor Green
Write-Host "Ahora puedes hacer 'docker-compose up -d' desplegando la app localmente." -ForegroundColor Yellow
