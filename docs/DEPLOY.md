# Deploy to one VPS (Ubuntu 24.04)

Needs: a VPS with 2 CPU, 4 GB RAM, 30 GB disk; a domain whose A record points
to the VPS IP; the repository on GitHub. Run every command as written.

## 1. Prepare the server (once)

```bash
ssh root@YOUR_SERVER_IP
```

```bash
adduser --disabled-password --gecos "" deploy && usermod -aG sudo deploy && mkdir -p /home/deploy/.ssh && cp ~/.ssh/authorized_keys /home/deploy/.ssh/ && chown -R deploy:deploy /home/deploy/.ssh
```

```bash
apt-get update && apt-get install -y ca-certificates curl git ufw && curl -fsSL https://get.docker.com | sh && usermod -aG docker deploy
```

```bash
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable
```

## 2. Get the code and settings

```bash
ssh deploy@YOUR_SERVER_IP
```

```bash
sudo mkdir -p /opt/scam-radar && sudo chown deploy:deploy /opt/scam-radar && git clone https://github.com/OWNER/scam-radar.git /opt/scam-radar
```

```bash
cd /opt/scam-radar/deploy && ./scripts/generate_env.sh scamradar.example.com team@example.com admin@example.com OWNER
```

The script writes `deploy/.env` with random passwords and prints the admin
password once. Every variable is explained in `deploy/.env.example` and
`backend/app/settings/.env.example`.

## 3. Start

Images are built by GitHub Actions and pushed to GitHub Container Registry.
If the packages are private, log in once with a token that has `read:packages`:

```bash
echo YOUR_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin
```

```bash
cd /opt/scam-radar/deploy && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d && ./scripts/wait_healthy.sh
```

Caddy gets the HTTPS certificate from Let's Encrypt by itself. Open
`https://your-domain` and check `https://your-domain/api/v1/health`.
The first analysis waits while the worker downloads the models (5–15 minutes).

## 4. Automatic deploys

In GitHub → Settings → Secrets → Actions add `DEPLOY_HOST` (server IP),
`DEPLOY_USER` (`deploy`) and `DEPLOY_SSH_KEY` (a private key whose public key is
in `/home/deploy/.ssh/authorized_keys`). Create the `production` environment.
After every green CI run on `main`, `deploy.yml` builds images, pushes them and
restarts the stack on the server.

## 5. Backups

```bash
crontab -e
```

Add this line (daily at 03:00, keeps 14 days):

```
0 3 * * * /opt/scam-radar/deploy/scripts/backup.sh >> /opt/scam-radar/deploy/backups/backup.log 2>&1
```

Restore: `./scripts/restore.sh backups/scamradar-YYYYMMDD-HHMMSS.sql.gz`.
Copy backups off the server too (for example `rsync` to a laptop weekly).

## 6. Log rotation

Docker logs are limited to 5 × 10 MB per service in the compose file. App log
files are rotated by the app (5 × 10 MB) and by logrotate:

```bash
sudo cp /opt/scam-radar/deploy/logrotate/scamradar /etc/logrotate.d/scamradar
```

## 7. Monitoring and uptime checklist

- `https://your-domain/api/v1/health` must return `"status":"ok"`. Add it to a free
  uptime checker (UptimeRobot, Better Stack) with a 5 minute interval.
- `/metrics` (Prometheus format) is reachable only inside the server:
  `docker compose -f docker-compose.prod.yml exec web wget -qO- http://api:8000/metrics`.
- Weekly: `docker compose -f docker-compose.prod.yml ps` (all healthy), `df -h` (disk under 80%),
  the backup log has no errors, `https://your-domain` certificate is valid.

## Mobile apps

- Android: `cd frontend && flutter build appbundle --release --dart-define=APP_ENV=prod --dart-define=API_BASE_URL=https://your-domain`.
  Sign it with your upload key (Android docs: "Sign your app") before Play Store upload.
- iOS (on a Mac with Xcode): `flutter build ipa --release --dart-define=APP_ENV=prod --dart-define=API_BASE_URL=https://your-domain`,
  then upload with Xcode Organizer. You need an Apple Developer account.
