# Deploy

## Local dev

```bash
docker compose up -d
# Logs
docker compose logs -f omni-controller
docker compose logs -f omniroute
```

## Public exposure (cloudflared tunnel)

Run two tunnels (or one tunnel with multiple services):

```bash
# Tunnel for omni-controller
cloudflared tunnel --url http://localhost:8081

# Tunnel for OmniRoute web UI (so Daviid can manage combos)
cloudflared tunnel --url http://localhost:20128
```

## Custom domain (future)

When Daviid buys a domain:

1. Configure DNS: `omni-controller.tudominio.com -> <vps-ip>`
2. Configure nginx as reverse proxy with HTTPS (Let's Encrypt)
3. Replace cloudflared with nginx + certbot

## Backups

omni-controller has no state to back up (no DB, no JSON files). All state
is in OmniRoute's SQLite — back that up if needed:

```bash
docker exec omni-controller-omniroute sqlite3 /path/to/db ".backup /backup/db.sqlite"
```
