#!/usr/bin/env bash
# One-time TLS setup for the Otodom bot on the deployment VM.
#
#   Domain : otodom-bot.duckdns.org  (DuckDNS A record must already point here)
#   Code   : /opt/otodom-bot
#
# Installs the HTTP reverse-proxy vhost, then runs certbot's nginx plugin, which
# obtains the Let's Encrypt cert AND edits the vhost in place to add the TLS
# server block + HTTP->HTTPS redirect. certbot's systemd timer handles renewals.
#
# Requires inbound 80 (HTTP-01 challenge + renewals) and 443 open on the VM.
#
# Usage:  sudo deploy/setup-tls.sh you@example.com
set -euo pipefail

DOMAIN=otodom-bot.duckdns.org
EMAIL=${1:?usage: setup-tls.sh <email-for-letsencrypt-notices>}
APP_DIR=/opt/otodom-bot

# 1. Packages — certbot plus its nginx plugin (the plugin is what edits nginx).
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# 2. Install the HTTP reverse-proxy vhost.
cp "$APP_DIR/deploy/nginx.conf.sample" /etc/nginx/sites-available/otodom-bot
ln -sf /etc/nginx/sites-available/otodom-bot /etc/nginx/sites-enabled/otodom-bot
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 3. Issue the cert; --nginx adds the TLS block + redirect to the vhost in place.
certbot --nginx -d "$DOMAIN" --redirect \
    --non-interactive --agree-tos -m "$EMAIL"

# 4. Confirm automatic renewal works (certbot installs a systemd timer).
certbot renew --dry-run

echo
echo "TLS ready: https://$DOMAIN"
echo "Set in /opt/otodom-bot/.env:  PUBLIC_URL=https://$DOMAIN"
