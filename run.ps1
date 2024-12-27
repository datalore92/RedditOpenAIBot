param(
    [switch]$clean
)

Write-Host "Building Docker image..."
if ($clean) {
    Write-Host "Performing clean build (no cache)..."
    docker build --no-cache -t reddit-bot-01 .
} else {
    docker build -t reddit-bot-01 .
}

Write-Host "Starting container..."
$containerId = docker run `
    --cap-add=NET_ADMIN `
    --device=/dev/net/tun `
    --env-file .env `
    -v "${PWD}/logs:/app/logs" `
    -v "${PWD}/logs:/var/log/openvpn" `
    --dns 8.8.8.8 `
    --dns 8.8.4.4 `
    --name reddit-bot `
    -d reddit-bot-01

Write-Host "Container started with ID: $containerId"
Write-Host "Press Ctrl+C to stop and remove container"

try {
    # Follow logs
    docker logs -f reddit-bot
}
finally {
    Write-Host "`nStopping and removing container..."
    docker stop reddit-bot
    docker rm reddit-bot
    Write-Host "Container cleaned up successfully"
}
