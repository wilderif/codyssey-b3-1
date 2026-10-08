#!/bin/bash
# Initialize Nginx on first boot through cloud-init, running as root.

# Stop on command failures, unset variables, or failures within pipelines.
set -euo pipefail

# Install packages without interactive prompts.
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx

# Create the static page served at /.
cat > /var/www/html/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Hello Cloud</title></head>
<body><h1>Hello Cloud</h1></body>
</html>
HTML

# Replace the default site; quoted heredocs preserve Nginx variables such as $uri.
cat > /etc/nginx/sites-available/default <<'NGINX'
# Serve HTTP on port 80 for requests to the instance's public IP.
server {
    listen 80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;

    # Serve existing files and return 404 for unknown paths.
    location / {
        try_files $uri $uri/ =404;
    }

    # Match only /health and return the fixed plain-text body OK with HTTP 200.
    location = /health {
        default_type text/plain;
        return 200 "OK";
    }
}
NGINX

# Check the configuration before restarting and enable startup on future boots.
nginx -t
systemctl enable nginx
systemctl restart nginx
# Report success only when the service is active.
systemctl is-active --quiet nginx
