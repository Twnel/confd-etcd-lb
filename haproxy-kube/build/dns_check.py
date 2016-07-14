#!/usr/bin/python

import socket
import dns.resolver
import re
import etcd
import os
import time
import subprocess
import json

# Basic query
def populate_etcd():
    # http://www.skippbox.com/using-a-kubernetes-api-python-client/
    # add to Dockerfile
    # curl -L https://storage.googleapis.com/kubernetes-release/release/v1.2.4/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
    # && chmod +x /usr/local/bin/kubectl \

    # modify DNS check to kube check
    # kubectl get -o json services
    #a = subprocess.Popen("kubectl get -o json services",stdout=subprocess.PIPE, shell=True)
    #b = str(a.stdout.read())
    #json.loads(b)
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=int(os.getenv('ETCD_SERVICE_PORT', 2379)))
    while True:
        for rdata in dns.resolver.query(os.getenv('DNS_DOMAIN', 'cluster.local'), 'SRV') :
            m = re.search(r'((\d+\s)+)(.*)', str(rdata), re.DOTALL)
            if m:
                parts = m.group(3).split('.')[1:3]
                client.set('/skydns/local/{}/{}/{}'.format(os.getenv('CLUSTER', 'beta'), parts[1], parts[0]), str({'host': '.'.join(parts)}))
        time.sleep(os.getenv('ETCD_SERVICE_INTERVAL', 10))

if __name__ == '__main__':
    populate_etcd()
