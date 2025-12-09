#!/bin/sh
# Docker entrypoint for DraftCraft Frontend
# Injects environment variables into built JavaScript files

set -e

# Environment variables to inject (default values for development)
export VITE_API_URL=${VITE_API_URL:-"http://localhost:8000"}

echo "🔧 Injecting environment variables..."
echo "VITE_API_URL: $VITE_API_URL"

# Find all JavaScript files and replace placeholder
# Vite builds environment variables as string literals, so we need to replace them at runtime
find /usr/share/nginx/html -type f -name '*.js' -exec sed -i \
  "s|__VITE_API_URL_PLACEHOLDER__|$VITE_API_URL|g" {} +

echo "✅ Environment variables injected"

# Execute the CMD
exec "$@"
