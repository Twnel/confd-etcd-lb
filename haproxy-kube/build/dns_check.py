#!/usr/bin/python

import socket
import dns.resolver
import re
import etcd
import os
import time
import subprocess
import json
from pprint import pformat, pprint
# Basic query
def populate_etcd():
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=int(os.getenv('ETCD_SERVICE_PORT', 2379)))
    while True:
        # modify DNS check to kube check
        # kubectl get -o json services
        kubectl_call = subprocess.Popen("kubectl get -o json services", stdout=subprocess.PIPE, shell=True)
        kubectl_str = str(kubectl_call.stdout.read())
        kubectl_services = json.loads(kubectl_str)
        for service in kubectl_services['items']:
            for match_port in (port for port in service['spec']['ports'] if 'internal' not in port['name']):
                pprint(client.set(
                    '/skydns/local/{}/{}/{}/{}:{}'.format(
                        service['metadata']['app_env'] if 'app_env' in service['metadata'] else 'beta',
                        service['metadata']['namespace'],
                        match_port['name'],
                        service['spec']['clusterIP'],
                        match_port['nodePort']
                    ),
                    str({
                        'host': '{}.{}'.format(service['metadata']['name'], service['metadata']['namespace']),
                        'port': match_port['port']
                    })
                ))

        time.sleep(os.getenv('ETCD_SERVICE_INTERVAL', 10))

if __name__ == '__main__':
    populate_etcd()