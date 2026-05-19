# Portable Coolify + Docker Compose deployment for WSL2 and VPS

This guide matches the local Coolify setup you already have: a Coolify control-plane container plus a `coolify-target` Docker-in-Docker (DinD) container that Coolify reaches over SSH. The same application Compose file can then run in three places with only environment-variable changes:

1. directly in WSL2/Docker Desktop for fast local checks;
2. through your local Coolify UI into the `coolify-target` DinD server;
3. through Coolify or plain Docker Compose on a cloud VPS.

References checked on 2026-05-17:

- Coolify self-hosted installation: <https://coolify.io/docs/get-started/installation>
- Coolify Docker Compose deployment behavior: <https://coolify.io/docs/knowledge-base/docker/compose>
- Coolify custom Compose overrides: <https://coolify.io/docs/knowledge-base/custom-compose-overrides>

## 1. Keep everything on the WSL2 Linux filesystem

Open Ubuntu/WSL2, not PowerShell, and keep the repo outside `/mnt/c/...`:

```bash
mkdir -p ~/apps
cd ~/apps
git clone <your-repo-url> UDESA_NEWALLBOTS
cd UDESA_NEWALLBOTS
```

Avoid running this from `C:\...` or `/mnt/c/...`. The Linux filesystem is faster and avoids bind-mount/file-watcher problems between Windows and Docker Desktop.

## 2. Start or replace your local Coolify stack

The repository now includes a cleaned-up version of the Compose stack you pasted:

- `deploy/local-coolify/docker-compose.yml`
- `deploy/local-coolify/Dockerfile.coolify-target`
- `deploy/local-coolify/docker/coolify-target-entrypoint.sh`
- `deploy/local-coolify/.env.example`

Do **not** commit your real `.env`; it contains secrets. Create it locally:

```bash
cd deploy/local-coolify
cp .env.example .env
```

Edit `.env` and replace every `replace_with_...` value. At minimum, generate new values for `APP_KEY`, `DB_PASSWORD`, `REDIS_PASSWORD`, `PUSHER_APP_ID`, `PUSHER_APP_KEY`, `PUSHER_APP_SECRET`, and `COOLIFY_USER_PASSWORD`.

Example generators:

```bash
printf 'APP_KEY=base64:%s\n' "$(openssl rand -base64 32)"
openssl rand -base64 32
openssl rand -hex 16
```

> Security note: the values pasted in chat should be considered exposed. Rotate them before using this setup beyond local testing.

Start Coolify:

```bash
docker compose up -d --build
```

Local ports:

| Purpose | Outer Windows/WSL URL | Inner target port |
|---|---:|---:|
| Coolify UI | `http://localhost:8080` | `coolify:8080` |
| Apps deployed inside `coolify-target` | `http://localhost:18080` | `coolify-target:8080` |
| Debug SSH to target | `localhost:2222` | `coolify-target:22` |

The important design is that Coolify itself can keep `APP_PORT=8080`, while apps deployed inside the DinD target also use `HTTP_PORT=8080`. The outer host sees the app through `LOCAL_APP_HTTP_PORT=18080`, so there is no local port collision.

## 3. Authorize Coolify to SSH into `coolify-target`

Your target entrypoint accepts `COOLIFY_PUBLIC_KEY` and writes it to both `root` and `coolify` users inside the target container.

After the first boot, extract Coolify's generated public key:

```bash
docker run --rm -v coolify-ssh:/ssh alpine \
  cat /ssh/keys/id.root@host.docker.internal.pub
```

Copy that output into `deploy/local-coolify/.env`:

```env
COOLIFY_PUBLIC_KEY=ssh-ed25519 ... root@coolify
```

Restart only the target so the key is installed:

```bash
docker compose up -d --build coolify-target
```

In the Coolify UI, add a server like this:

| Field | Value |
|---|---|
| Name | `local-dind` |
| Host/IP | `coolify-target` |
| Port | `22` |
| User | `root` |
| Private key | the generated `root@host.docker.internal` key in Coolify |

Because `coolify` and `coolify-target` are on the same Compose network, the hostname `coolify-target` resolves from inside the Coolify container.

## 4. Put app data inside the target server

When Coolify deploys to the local DinD target, bind mounts such as `/data/all-bots/...` are paths **inside `coolify-target`**, not on your Windows filesystem. Copy the private data into the target volume:

```bash
cd ../../
docker exec coolify-target mkdir -p /data/all-bots/config/gcp /data/all-bots/sharedData
docker cp config/gcp/. coolify-target:/data/all-bots/config/gcp/
docker cp sharedData/. coolify-target:/data/all-bots/sharedData/
```

The same paths are used on a VPS, so migration is simple:

```bash
sudo mkdir -p /data/all-bots/config/gcp /data/all-bots/sharedData
# copy config/gcp and sharedData to those directories on the VPS
```

## 5. Deploy this app through your local Coolify

Create a Docker Compose application/resource in Coolify and point it to this repository.

Use this Compose file path:

```text
docker-compose.coolify.yaml
```

Set these environment variables in the Coolify resource:

```env
HTTP_PORT=8080
HTTP_BIND_ADDRESS=0.0.0.0
ALLBOTS_DATA_ROOT=/data/all-bots/sharedData
ALLBOTS_GCP_CONFIG_DIR=/data/all-bots/config/gcp
```

Deploy to the `local-dind` server. Then open:

- `http://localhost:18080/prod/epu/en/`
- `http://localhost:18080/prod/epu/es/`
- `http://localhost:18080/prod/nowcast/en/`
- `http://localhost:18080/prod/nowcast/es/`
- `http://localhost:18080/health`

Only the `gateway` service publishes a port. The dashboards and data pipeline stay on the internal Docker network.

## 6. Run the same app directly in WSL2 without Coolify

For a direct local smoke test on your Docker Desktop daemon, use a different host port because the Coolify UI already uses `8080`:

```bash
HTTP_BIND_ADDRESS=127.0.0.1 \
HTTP_PORT=18080 \
ALLBOTS_DATA_ROOT=./sharedData \
ALLBOTS_GCP_CONFIG_DIR=./config/gcp \
docker compose -f docker-compose.coolify.yaml up --build -d
```

Open `http://localhost:18080/health`.

## 7. Move to a VPS with minimal changes

On the VPS, install Docker/Coolify, clone this repo, and create the same data directories:

```bash
sudo mkdir -p /data/all-bots/config/gcp /data/all-bots/sharedData
cd ~/apps
git clone <your-repo-url> UDESA_NEWALLBOTS
cd UDESA_NEWALLBOTS
```

Copy your private folders to the VPS:

```bash
# from local WSL2, adjust user/host/path
rsync -av config/gcp/ user@your-vps:/data/all-bots/config/gcp/
rsync -av sharedData/ user@your-vps:/data/all-bots/sharedData/
```

Use the same Coolify resource environment on the VPS:

```env
HTTP_PORT=8080
HTTP_BIND_ADDRESS=0.0.0.0
ALLBOTS_DATA_ROOT=/data/all-bots/sharedData
ALLBOTS_GCP_CONFIG_DIR=/data/all-bots/config/gcp
```

If you are exposing the app directly, open one inbound app port:

```bash
sudo ufw allow 8080/tcp
```

If you later put this behind Coolify's proxy/domain routing, close the direct `8080` firewall rule and let Coolify handle `80/443`.

## 8. Coolify self-host override for official installs

For a standard official Coolify install under `/data/coolify/source`, keep persistent customizations in:

```text
/data/coolify/source/docker-compose.custom.yml
```

This repository includes `deploy/coolify-selfhost/docker-compose.custom.yml` for predictable Coolify UI binding. Validate before applying:

```bash
sudo cp deploy/coolify-selfhost/docker-compose.custom.yml /data/coolify/source/docker-compose.custom.yml
cd /data/coolify/source
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.custom.yml \
  config
```

## 9. Daily commands

Local Coolify control plane:

```bash
cd deploy/local-coolify
docker compose ps
docker compose logs -f coolify
docker compose logs -f coolify-target
docker compose down
```

Direct app Compose:

```bash
docker compose -f docker-compose.coolify.yaml ps
docker compose -f docker-compose.coolify.yaml logs -f gateway
docker compose -f docker-compose.coolify.yaml down
```


## 10. Multi-tenant VPS alignment (2–3 clients)

If your next step is hosting multiple clients on one VPS, this repository's setup is a good starting point but should be used as a per-client template.

See `docs/deployment/coolify-multitenant-fit.md` for a direct mapping of your isolation model (network-per-client, domain-per-client, resource limits, per-client volumes, onboarding/offboarding).
