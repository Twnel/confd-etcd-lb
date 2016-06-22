#!/bin/bash

# Fail hard and fast
set -eo pipefail

export ETCD_PORT=${ETCD_PORT:-2379}
export HOST_IP=${HOST_IP:-172.17.42.1}
export ETCD=$HOST_IP:$ETCD_PORT
export DOMAIN=${DOMAIN:-example.com}
export REGION=${REGION:-api}
export CLUSTER=${CLUSTER:-beta}
export HTPASSWD="$(openssl passwd -apr1 ${HTPASSWD:-password})"

# Specify where we will install
# the xip.io certificate
SSL_DIR="/etc/haproxy/certs"

# Set the wildcarded domain
# we want to use
MAIN_DOMAIN="*.${DOMAIN}"

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

echo "admin:${HTPASSWD}" > /etc/haproxy/.htpasswd
openssl req -subj "$(echo -n "$SUBJ" | tr "\n" "/")" -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$SSL_DIR/default.key" -out "$SSL_DIR/default.crt" -passin pass:$PASSPHRASE

echo "[haproxy] booting container. ETCD: $ETCD"

# Loop until confd has updated the haproxy config
until confd -onetime -node $ETCD; do
  echo "[haproxy] waiting for confd to refresh haproxy.conf"
  sleep 5
done

# Run confd in the background to watch the upstream servers
confd -interval 10 -node $ETCD &
echo "[haproxy] confd is listening for changes on etcd..."

# Start haproxy
echo "[haproxy] starting haproxy service..."
exec /usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg

# Tail all haproxy log files
tail -f /var/log/haproxy/*.log
