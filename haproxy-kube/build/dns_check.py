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
    kubectl_call_pods = "kubectl --namespace {} get -o json pods --selector=app={}"
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=int(os.getenv('ETCD_SERVICE_PORT', 2379)))
    while True:
        # modify DNS check to kube check
        # kubectl get -o json services
        kubectl_call = subprocess.Popen("kubectl get --all-namespaces -o json services", stdout=subprocess.PIPE, shell=True)
        kubectl_str = str(kubectl_call.stdout.read())
        kubectl_services = json.loads(kubectl_str)
        #for key in (app['key'] for app in client.get('/skydns/local/beta/ui')._children):
        #    key.split('/')[-1]
        for service in kubectl_services['items']:
            for match_port in (port for port in service['spec']['ports'] if 'name' in port and 'internal' not in port['name']):
                try:
                    kubectl_get_pods = subprocess.Popen(kubectl_call_pods.format(service['metadata']['namespace'], service['spec']['selector']['app']), stdout=subprocess.PIPE, shell=True)
                    kubectl_str_pods = str(kubectl_get_pods.stdout.read())
                    kubectl_pods = json.loads(kubectl_str_pods)
                    for pod in kubectl_pods['items']:
                        pprint(client.set(
                            '/skydns/local/{}/{}/{}/{}:{}'.format(
                                service['metadata']['app_env'] if 'app_env' in service['metadata'] else 'beta',
                                service['metadata']['namespace'],
                                match_port['name'],
                                pod['status']['podIP'],
                                match_port['port']
                            ),
                            json.dumps({
                                'host': pod['status']['podIP'],
                                'port': match_port['port']
                            })
                        ))
                except KeyError:
                    pprint('Error: {}'.format(match_port['name']))

        time.sleep(os.getenv('ETCD_SERVICE_INTERVAL', 10))

if __name__ == '__main__':
    populate_etcd()