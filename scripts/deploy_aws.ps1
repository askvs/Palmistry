param([string]$Sha = "latest", [string]$Region = $env:AWS_REGION)
if (-not $Region) { $Region = "us-east-1" }
$account = (aws sts get-caller-identity --query Account --output text)
$backend = "$account.dkr.ecr.$Region.amazonaws.com/palmistry-backend:$Sha"
$frontend = "$account.dkr.ecr.$Region.amazonaws.com/palmistry-frontend:$Sha"
Write-Host "Backend: $backend"
Write-Host "Frontend: $frontend"
aws ecs update-service --region $Region --cluster palmistry --service backend --force-new-deployment
aws ecs update-service --region $Region --cluster palmistry --service frontend --force-new-deployment
