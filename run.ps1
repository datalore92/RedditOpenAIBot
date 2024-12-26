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
docker run `
    --cap-add=NET_ADMIN `
    --device=/dev/net/tun `
    --env-file .env `
    -v "${PWD}/logs:/app/logs" `
    -v "${PWD}/logs:/var/log/openvpn" `
    --dns 8.8.8.8 `
    --dns 8.8.4.4 `
    reddit-bot-01
