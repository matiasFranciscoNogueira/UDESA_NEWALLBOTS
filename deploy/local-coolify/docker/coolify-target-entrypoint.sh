#!/bin/sh
set -eu

mkdir -p /root/.ssh /run/sshd /data/all-bots/sharedData /data/all-bots/config/gcp
chmod 700 /root/.ssh

if [ -n "${COOLIFY_PUBLIC_KEY:-}" ]; then
  printf '%s\n' "$COOLIFY_PUBLIC_KEY" > /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

if ! id coolify >/dev/null 2>&1; then
  adduser -D -s /bin/sh coolify
fi

echo "coolify:${COOLIFY_USER_PASSWORD:-coolify-local-target}" | chpasswd
addgroup coolify docker >/dev/null 2>&1 || true

mkdir -p /home/coolify/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
  cp /root/.ssh/authorized_keys /home/coolify/.ssh/authorized_keys
  chmod 600 /home/coolify/.ssh/authorized_keys
else
  : > /home/coolify/.ssh/authorized_keys
  chmod 600 /home/coolify/.ssh/authorized_keys
fi
chown -R coolify:coolify /home/coolify/.ssh
chmod 700 /home/coolify/.ssh

ssh-keygen -A >/dev/null 2>&1
/usr/sbin/sshd

exec dockerd-entrypoint.sh "$@"
