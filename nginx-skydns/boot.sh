#!/bin/bash

# Fail hard and fast
set -eo pipefail

confd_resolve () {
  export ETCD_SERVICE_PORT=${ETCD_SERVICE_PORT:-2379}
  export ETCD_SERVICE_HOST=${ETCD_SERVICE_HOST:-127.0.0.1}
  export ETCD_RESOLVE=$(host ${ETCD_SERVICE_HOST} | awk '/has address/ { print $4 }')
  export ETCD_SERVICE_RESOLVE=${ETCD_RESOLVE:-${ETCD_SERVICE_HOST}}
  export ETCD_SERVICE_ADDR=${ETCD_SERVICE_RESOLVE}:${ETCD_SERVICE_PORT}
}
confd_resolve
export DOMAIN=${DOMAIN:-example.com}
export REGION=${REGION:-api}
export CLUSTER=${CLUSTER:-beta}
export HTPASSWD="$(openssl passwd -apr1 ${HTPASSWD:-password})"

# Specify where we will install
# the xip.io certificate
SSL_DIR="/etc/nginx/certs"

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

echo "admin:${HTPASSWD}" > /etc/nginx/.htpasswd
openssl req -subj "$(echo -n "$SUBJ" | tr "\n" "/")" -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$SSL_DIR/default.key" -out "$SSL_DIR/default.crt" -passin pass:$PASSPHRASE

echo "[nginx] booting container. ETCD: $ETCD_SERVICE_ADDR"

# Loop until confd has updated the nginx config
#until confd -onetime -node $ETCD_SERVICE_ADDR; do
echo "[nginx] waiting for confd to refresh nginx.conf"
#  sleep 5
#done

# Run confd in the background to watch the upstream servers
# confd -interval 10 -node $ETCD_SERVICE_ADDR &
confd_interval () {
  while true; do {
    confd_resolve
    confd -onetime -node $ETCD_SERVICE_ADDR; sleep 10;
  }; done;
}
nohup confd_interval 2>&1 &
echo "[nginx] confd is listening for changes on etcd..."

# Start nginx
echo "[nginx] starting nginx service..."
service nginx start

# Tail all nginx log files
tail -f /var/log/nginx/*.log
