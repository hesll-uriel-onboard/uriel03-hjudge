#!/bin/bash
set -e

# Save Heroku's assigned port before FlareSolverr overrides PORT
WEB_PORT=${PORT:-8000}

# Start FlareSolverr in background on 8191
PORT=8191 /usr/bin/dumb-init -- /usr/local/bin/python -u /app/flaresolverr.py &

echo "Waiting for FlareSolverr..."
until curl -s http://localhost:8191/health > /dev/null; do
    sleep 2
done
echo "FlareSolverr ready."

cd /home/hjudge
exec uv run litestar --app hjudge.app:app run --host 0.0.0.0 --port "$WEB_PORT"
