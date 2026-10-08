#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx

cat > /var/www/html/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Hello Cloud</title></head>
<body><h1>Hello Cloud</h1></body>
</html>
HTML

cat > /etc/nginx/sites-available/default <<'NGINX'
server {
    listen 80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location = /health {
        default_type text/plain;
        return 200 "OK";
    }
}
NGINX

nginx -t
systemctl enable nginx
systemctl restart nginx
systemctl is-active --quiet nginx
