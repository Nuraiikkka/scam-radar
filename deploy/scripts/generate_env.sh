#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [ -f .env ]; then
  echo ".env already exists, not overwriting it"
  exit 1
fi

if [ "$#" -ne 4 ]; then
  echo "usage: $0 <domain> <acme-email> <admin-email> <github-owner>"
  exit 1
fi

owner=$(echo "$4" | tr '[:upper:]' '[:lower:]')
cp .env.example .env
sed -i "s|^SCAMRADAR_DOMAIN=.*|SCAMRADAR_DOMAIN=$1|" .env
sed -i "s|^ACME_EMAIL=.*|ACME_EMAIL=$2|" .env
sed -i "s|^SCAMRADAR_ADMIN_EMAIL=.*|SCAMRADAR_ADMIN_EMAIL=$3|" .env
sed -i "s|^BACKEND_IMAGE=.*|BACKEND_IMAGE=ghcr.io/$owner/scam-radar-backend|" .env
sed -i "s|^WEB_IMAGE=.*|WEB_IMAGE=ghcr.io/$owner/scam-radar-web|" .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^SCAMRADAR_SECRET_KEY=.*|SCAMRADAR_SECRET_KEY=$(openssl rand -hex 32)|" .env
admin_password=$(openssl rand -base64 18 | tr -d '/+=')
sed -i "s|^SCAMRADAR_ADMIN_PASSWORD=.*|SCAMRADAR_ADMIN_PASSWORD=$admin_password|" .env
chmod 600 .env
echo ".env created. Admin password: $admin_password"
echo "Save the admin password in your password manager now."
