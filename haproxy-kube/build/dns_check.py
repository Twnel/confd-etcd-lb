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
def loop_services(kubectl_services):
    for service in kubectl_services:
        for match_port in (port for port in service['spec']['ports'] if 'name' in port and 'internal' not in port['name']):
            yield service, match_port

def populate_etcd():
    kubectl_call_pods = "kubectl --namespace {} get -o json pods --selector=app={}"
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=int(os.getenv('ETCD_SERVICE_PORT', 2379)))
    while True:
        # modify DNS check to kube check
        # kubectl get -o json services
        kubectl_call = subprocess.Popen("kubectl get --all-namespaces -o json services", stdout=subprocess.PIPE, shell=True)
        kubectl_str = str(kubectl_call.stdout.read())
        kubectl_services = json.loads(kubectl_str)
        def set_etcd_services():
            for service, match_port in loop_services(kubectl_services['items']):
                try:
                    kubectl_get_pods = subprocess.Popen(kubectl_call_pods.format(service['metadata']['namespace'], service['spec']['selector']['app']), stdout=subprocess.PIPE, shell=True)
                    kubectl_str_pods = str(kubectl_get_pods.stdout.read())
                    kubectl_pods = json.loads(kubectl_str_pods)
                    for pod in kubectl_pods['items']:
                        try:
                            print service['metadata']
                            app_env = service['metadata']['annotations']['app_env']
                        except KeyError:
                            app_env = 'beta'
                        new_service = '/skydns/local/{}/{}/{}/{}:{}'.format(
                            app_env,
                            service['metadata']['namespace'],
                            match_port['name'],
                            pod['status']['podIP'],
                            match_port['port']
                        )
                        try:
                            pprint(client.write(
                                new_service,
                                json.dumps({
                                    'host': pod['status']['podIP'],
                                    'port': match_port['port']
                                }),
                                prevExist = False
                            ))
                        except etcd.EtcdAlreadyExist:
                            pprint('Key exists: {}'.format(new_service))
                        yield new_service
                except KeyError as e:
                    pprint('Error: {}, {}'.format(match_port['name'], e.message))
        cluster_key = '/skydns/local/{}'.format(os.getenv('CLUSTER', 'beta'))
        try:
            etcd_leaves = client.read(cluster_key, recursive=True).leaves
            for key in set(
                (app.key for app in etcd_leaves if ':' in app.key.split('/')[-1])).difference(
                    set_etcd_services()):
                client.delete(key)
        except etcd.EtcdKeyNotFound:
            client.write(cluster_key, None, dir=True)
            pprint('NO key: {}'.format(cluster_key))

        time.sleep(os.getenv('ETCD_SERVICE_INTERVAL', 10))

if __name__ == '__main__':
    populate_etcd()