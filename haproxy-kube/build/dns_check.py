#!/usr/bin/python

import socket
import dns.resolver
import re
import etcd
import os
import time

# Basic query
def populate_etcd():
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=os.getenv('ETCD_SERVICE_PORT', 2379))
    while True:
        for rdata in dns.resolver.query(os.getenv('DNS_DOMAIN', 'cluster.local'), 'SRV') :
            m = re.search(r'((\d+\s)+)(.*)', str(rdata), re.DOTALL)
            if m:
                parts = m.group(3).split('.')[1:3]
                client.set('/services/{}/{}'.format(parts[1], parts[0]), str({'host': '.'.join(parts)}))
        time.sleep(os.getenv('ETCD_SERVICE_INTERVAL', 10)

if __main__ == '__name__':
    populate_etcd()