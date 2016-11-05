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
        try:
            subsets = service['subsets'][0]
            for match_port in (port for port in subsets['ports'] if 'internal' not in port['name']):
                yield service, match_port, subsets
        except Exception as e:
            pprint('Service not configured: {} ::: {}'.format(service['metadata']['name'], e.message))

def populate_etcd():
    #kubectl_call_pods = "kubectl --namespace {} get -o json pods --selector=app={}"
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=int(os.getenv('ETCD_SERVICE_PORT', 2379)))
    app_env = os.getenv('CLUSTER', 'beta')
    while True:
        # modify DNS check to kube check
        # kubectl get -o json services
        kubectl_call = subprocess.Popen("kubectl get --all-namespaces -o json endpoints", stdout=subprocess.PIPE, shell=True)
        kubectl_str = str(kubectl_call.stdout.read())
        kubectl_services = json.loads(kubectl_str)
        def set_etcd_services():
            for service, match_port, subsets in loop_services(kubectl_services['items']):
                try:
                    pprint(service['metadata'])
                    #kubectl_get_pods = subprocess.Popen(kubectl_call_pods.format(service['metadata']['namespace'], service['spec']['selector']['app']), stdout=subprocess.PIPE, shell=True)
                    #kubectl_str_pods = str(kubectl_get_pods.stdout.read())
                    kubectl_pods = subsets['addresses'] #json.loads(kubectl_str_pods)
                    for pod in kubectl_pods:
                        new_service = '/skydns/local/{}/{}/{}/{}:{}'.format(
                            app_env,
                            service['metadata']['namespace'],
                            match_port['name'],
                            pod['ip'],
                            match_port['port']
                        )
                        try:
                            pprint(client.write(
                                new_service,
                                json.dumps({
                                    'host': pod['ip'],
                                    'port': match_port['port']
                                }),
                                prevExist = False
                            ))
                        except etcd.EtcdAlreadyExist:
                            pprint('Key exists: {}'.format(new_service))
                        except etcd.EtcdException as e:
                            pprint('etcd error: {} ::: {}'.format(e.message, new_service))
                        except etcd.Exception as e:
                            pprint('Unhandled exception: {} ::: {}'.format(e.message, new_service))
                        yield new_service
                except KeyError as e:
                    pprint('Error: {}, {}'.format(match_port['name'], e.message))
        cluster_key = '/skydns/local/{}'.format(app_env)
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