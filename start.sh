#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

docker compose up -d --build

LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo ""
echo "  Time Collector is running."
echo "  Local:    http://localhost:8000"
echo "  Network:  http://${LOCAL_IP}:8000"
echo ""
echo "  Logs:     docker compose logs -f"
echo "  Stop:     docker compose down"
echo ""
