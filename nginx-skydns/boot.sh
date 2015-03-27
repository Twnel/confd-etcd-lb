#!/bin/bash

# Fail hard and fast
set -eo pipefail

export ETCD_PORT=${ETCD_PORT:-4001}
export HOST_IP=${HOST_IP:-172.17.42.1}
export ETCD=$HOST_IP:4001
export DOMAIN=${DOMAIN:-core}
export HTPASSWD=${HTPASSWD:-password}

# Specify where we will install
# the xip.io certificate
SSL_DIR="/etc/nginx/certs"

# Set the wildcarded domain
# we want to use
MAIN_DOMAIN="*.twnel.com"

# A blank passphrase
PASSPHRASE=""

# Set our CSR variables
SUBJ="
C=US
ST=Connecticut
O=
localityName=New Haven
commonName=$MAIN_DOMAIN
organizationalUnitName=
emailAddress=
"

echo "admin:$(openssl passwd -apr1 \"${HTPASSWD}\")" > /etc/nginx/.htpasswd
openssl req -subj "$(echo -n "$SUBJ" | tr "\n" "/")" -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$SSL_DIR/default.key" -out "$SSL_DIR/default.crt" -passin pass:$PASSPHRASE

echo "[nginx] booting container. ETCD: $ETCD"

# Loop until confd has updated the nginx config
until confd -onetime -node $ETCD -config-file /etc/confd/conf.d/nginx.toml; do
  echo "[nginx] waiting for confd to refresh nginx.conf"
  sleep 5
done

# Run confd in the background to watch the upstream servers
confd -interval 10 -node $ETCD -config-file /etc/confd/conf.d/nginx.toml &
echo "[nginx] confd is listening for changes on etcd..."

# Start nginx
echo "[nginx] starting nginx service..."
service nginx start

# Tail all nginx log files
tail -f /var/log/nginx/*.log
