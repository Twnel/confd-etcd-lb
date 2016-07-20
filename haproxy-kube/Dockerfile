FROM haproxy
MAINTAINER Ericson Cepeda <ericson@picorb.com>

# Install haproxy
RUN apt-get update

RUN         apt-get install -y curl wget python-pip ca-certificates openssl tar && \
            wget https://github.com/coreos/etcd/releases/download/v2.0.10/etcd-v2.0.10-linux-amd64.tar.gz && \
            tar xzvf etcd-v2.0.10-linux-amd64.tar.gz && \
            mv etcd-v2.0.10-linux-amd64/etcd* /bin/
VOLUME      /data

ADD build/run-etcd.sh /bin/run.sh
RUN chmod +x /bin/run.sh

# http://www.skippbox.com/using-a-kubernetes-api-python-client/
RUN curl -L https://storage.googleapis.com/kubernetes-release/release/v1.2.4/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir -p /var/log/supervisor
ADD build/supervisord.conf /usr/local/supervisord.conf

# Install confd
RUN curl -L https://github.com/kelseyhightower/confd/releases/download/v0.10.0/confd-0.10.0-linux-amd64 -o confd
RUN mv confd /usr/local/bin/confd
RUN chmod +x /usr/local/bin/confd

# Create directories
RUN mkdir -p /etc/confd/conf.d
RUN mkdir -p /etc/confd/templates

# Add confd files
ADD build/*.tmpl /etc/confd/templates/
ADD build/*.toml /etc/confd/conf.d/
#ADD build/haproxy.cfg /etc/haproxy/

# Remove default site
# RUN rm -f /etc/haproxy/sites-enabled/default

# Add boot script
ADD build/boot.sh /opt/boot.sh
RUN chmod +x /opt/boot.sh
ADD build/dns_check.py /opt/dns_check.py
RUN chmod +x /opt/dns_check.py

VOLUME ["/etc/haproxy/certs", "/var/log/etcd"]

# Run the boot script
CMD ["/usr/local/bin/supervisord", "-n"]
