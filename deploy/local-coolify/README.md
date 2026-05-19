# Local Coolify control plane for WSL2

This folder contains the portable local Coolify setup used by the main deployment guide.

## Start

```bash
cp .env.example .env
# edit .env and replace all placeholder secrets
docker compose up -d --build
```

Open Coolify at <http://localhost:8080>.

## Authorize the local DinD target

```bash
docker run --rm -v coolify-ssh:/ssh alpine \
  cat /ssh/keys/id.root@host.docker.internal.pub
```

Paste that public key into `.env` as `COOLIFY_PUBLIC_KEY`, then restart the target:

```bash
docker compose up -d --build coolify-target
```

Add the server in Coolify using host `coolify-target`, port `22`, user `root`, and the generated Coolify private key.

## App port mapping

Apps deployed inside the DinD target should bind `HTTP_PORT=8080`. The outer WSL2/Windows host reaches that target port through `LOCAL_APP_HTTP_PORT=18080`, so the app URL is <http://localhost:18080>.
