# Deploying to the VPS

This puts the app at `https://mystery.67-217-243-44.nip.io`, next to whatever else the server runs. Nothing else on the server is changed or restarted: the app gets its own container, its own Postgres user and database, and its own nginx site.

Run everything as root (or with `sudo`) over SSH. It takes about 30 minutes the first time.

| Piece | Where |
| --- | --- |
| Code | `/root/murdermystery`, the `production` branch |
| Container | `murdermystery`, host networking, listens on `127.0.0.1:8100` only, capped at 300 MB |
| Database | `murdermystery` on the server's Postgres, owned by the `murdermystery` user |
| Web | nginx site `murdermystery`, HTTPS from Let's Encrypt via certbot |
| Start on boot | systemd unit `murdermystery.service` |

## 0. The production branch

The server deploys from a `production` branch. Create it from this branch once, either on GitHub (Branches → New branch, source `ccr-8b776a1d-g98lpx`) or locally:

```
git push origin ccr-8b776a1d-g98lpx:production
```

`main` keeps serving the old static site on GitHub Pages.

## 1. Check the server

```bash
systemctl status nginx --no-pager | head -3      # want: active (running)
ls /etc/nginx/sites-enabled/
sudo ss -tlnp | grep -E ':(80|443|8100) '         # 80 and 443 should be nginx; 8100 must be free
sudo ufw status                                  # if active, 80 and 443 must be allowed
free -h                                          # want at least 400 MB available
df -h /                                          # want at least 2 GB free for the image
docker compose version
systemctl status postgresql --no-pager | head -3
```

If the firewall is on and 80 or 443 isn't listed: `sudo ufw allow 'Nginx Full'`.

## 2. Database

```bash
sudo -u postgres psql <<'SQL'
CREATE USER murdermystery PASSWORD 'pick-a-long-password';
CREATE DATABASE murdermystery OWNER murdermystery;
REVOKE CONNECT ON DATABASE murdermystery FROM PUBLIC;
SQL
```

The new user owns only its own database and can't read any other. Check it can log in over the loopback address the app uses:

```bash
psql "postgres://murdermystery:pick-a-long-password@127.0.0.1:5432/murdermystery" -c 'select 1'
```

If that says `password authentication failed` or `no pg_hba.conf entry`, add this line near the top of the rules in `/etc/postgresql/*/main/pg_hba.conf`, then `systemctl reload postgresql`:

```
host  murdermystery  murdermystery  127.0.0.1/32  scram-sha-256
```

## 3. App

```bash
cd /root
git clone -b production https://github.com/epheonix380/murdermystery.git
cd murdermystery
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # use this for DJANGO_SECRET_KEY
nano .env
```

`.env` should end up as:

```
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<the long random string>
DJANGO_ALLOWED_HOSTS=mystery.67-217-243-44.nip.io
DATABASE_URL=postgres://murdermystery:pick-a-long-password@127.0.0.1:5432/murdermystery
```

```bash
chmod 600 .env
docker compose up -d --build
docker compose logs -f          # wait for "Listening on TCP address 127.0.0.1:8100", then Ctrl-C
curl http://127.0.0.1:8100/healthz    # want: ok
```

On every start the container runs the database migrations and loads the cases in `cases/`, then serves.

## 4. nginx

```bash
cp deploy/nginx-murdermystery.conf /etc/nginx/sites-available/murdermystery
ln -s /etc/nginx/sites-available/murdermystery /etc/nginx/sites-enabled/murdermystery
nginx -t && systemctl reload nginx
curl -I http://mystery.67-217-243-44.nip.io/      # want: HTTP/1.1 200 OK
```

The site config forwards WebSockets (`Upgrade` headers, 1-hour read timeout) so phones stay connected all evening.

## 5. HTTPS

```bash
certbot --nginx -d mystery.67-217-243-44.nip.io
```

Pick "redirect" if certbot asks. It renews itself; `certbot renew --dry-run` checks that.

Open `https://mystery.67-217-243-44.nip.io` on your phone: you should see the case browser with the Hollowpine map.

## 6. Start on boot

```bash
cp deploy/murdermystery.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable murdermystery
```

`restart: unless-stopped` in `docker-compose.yml` also restarts the container if it crashes.

## 7. Admin login (optional)

The Django admin at `/admin/` lets you hide or show cases and look at games.

```bash
docker compose exec web python manage.py createsuperuser
```

## Updating

Merge changes into `production`, then on the server:

```bash
cd /root/murdermystery
git pull
docker compose up -d --build
```

Migrations and case imports run on start. To change or add a case, edit its folder under `cases/`, push, and update the same way; a case with problems is listed in `docker compose logs` and left out, while the rest still load.

## Day to day

```bash
docker ps --filter name=murdermystery            # want: Up ... (healthy)
docker compose logs --tail 100 -f
docker stats --no-stream murdermystery           # memory against the 300 MB cap
```

Back up the database (games and players; cases live in git):

```bash
sudo -u postgres pg_dump murdermystery > murdermystery-$(date +%F).sql
```

## Rolling back

```bash
git log --oneline -5
git checkout <previous commit>
docker compose up -d --build
```

Migrations only ever add to the database in this app so far, so running older code on a newer database is safe for now. Before going back past a migration, check the release notes.

## Removing it

```bash
systemctl disable --now murdermystery
docker compose down --rmi local
rm /etc/nginx/sites-enabled/murdermystery /etc/nginx/sites-available/murdermystery /etc/systemd/system/murdermystery.service
systemctl reload nginx
certbot delete --cert-name mystery.67-217-243-44.nip.io
sudo -u postgres psql -c 'DROP DATABASE murdermystery' -c 'DROP USER murdermystery'
```
