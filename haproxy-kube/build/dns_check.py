#!/usr/bin/python

import socket
import dns.resolver
import re
import etcd
import os
import time
import subprocess
import json
import sys
import logging as log

APP_ENV = os.getenv('CLUSTER', 'beta')
DEBUG = 1 if APP_ENV == 'beta' else __debug__
log.basicConfig(stream=sys.stdout, level=log.DEBUG if DEBUG else log.INFO)

# Basic query
def loop_services(kubectl_services):
    for service in kubectl_services:
        for match_port in (port for port in service['spec']['ports'] if 'name' in port and 'internal' not in port['name']):
            yield service, match_port

def write_host(service, match_port, service_host, client):
    new_service = '/skydns/local/{}/{}/{}/{}:{}'.format(
        APP_ENV,
        service['metadata']['namespace'],
        match_port['name'],
        service_host,
        match_port['port']
    )
    try:
        log.info(client.write(
            new_service,
            json.dumps({
                'host': service_host,
                'port': match_port['port']
            }),
            prevExist = False
        ))
    except etcd.EtcdAlreadyExist:
        log.info('Key exists: {}'.format(new_service))
    except etcd.EtcdException as e:
        log.info('etcd error: {} ::: {}'.format(e.message, new_service))
    except etcd.Exception as e:
        log.error('Unhandled exception: {} ::: {}'.format(e.message, new_service))
    return new_service

def set_etcd_services(kubectl_services, client):
    for service, match_port in loop_services(kubectl_services['items']):
        try:
            # Verify whether service uses sticky sessions
            if service['spec']['sessionAffinity'] == 'ClientIP':
                try:
                    kubectl_call = subprocess.Popen(
                        "kubectl get --namespace {} -o json endpoints {}".format(
                            service['metadata']['namespace'],
                            match_port['name']), stdout=subprocess.PIPE, shell=True)
                    kubectl_str = str(kubectl_call.stdout.read())
                    kubectl_service = json.loads(kubectl_str)
                except ValueError as e:
                    log.debug('Service not expected: {}, {}'.format(match_port['name'], e.message))
                    continue
                # Retrieve service related pods
                subsets = kubectl_service['subsets'][0]
                kubectl_pods = subsets['addresses']
                match_port = subsets['ports'][0]
                for pod in kubectl_pods:
                    yield write_host(service, match_port, pod['ip'], client)
            else:
                service_host = '{}.{}'.format(
                    service['metadata']['name'],
                    service['metadata']['namespace'])
                yield write_host(service, match_port, service_host, client)
        except KeyError as e:
            log.debug('Error: {}, {}'.format(match_port['name'], e.message))


def populate_etcd():
    client = etcd.Client(host=os.getenv('ETCD_SERVICE_HOST', 'etcd'), port=int(os.getenv('ETCD_SERVICE_PORT', 2379)))
    while True:
        try:
            # modify DNS check to kube check
            kubectl_call = subprocess.Popen("kubectl get --all-namespaces -o json services", stdout=subprocess.PIPE, shell=True)
            kubectl_str = str(kubectl_call.stdout.read())
            kubectl_services = json.loads(kubectl_str)
            cluster_key = '/skydns/local/{}'.format(APP_ENV)
            etcd_leaves = client.read(cluster_key, recursive=True).leaves
            for key in set(
                (app.key for app in etcd_leaves if ':' in app.key.split('/')[-1])).difference(
                    set_etcd_services(kubectl_services, client)):
                client.delete(key)
        except etcd.EtcdKeyNotFound:
            client.write(cluster_key, None, dir=True)
            log.info('NO key: {}'.format(cluster_key))
        except ValueError as e:
            log.exception(e)

        time.sleep(os.getenv('ETCD_SERVICE_INTERVAL', 10))

if __name__ == '__main__':
    populate_etcd()
