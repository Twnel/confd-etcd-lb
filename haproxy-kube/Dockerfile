FROM phusion/baseimage:latest
MAINTAINER Ericson Cepeda <ericson@picorb.com>

# Install haproxy
RUN apt-get update
RUN apt-get install -y curl

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
ADD build/haproxy.cfg /etc/haproxy/

# Remove default site
# RUN rm -f /etc/haproxy/sites-enabled/default

# Add boot script
ADD ./boot.sh /opt/boot.sh
RUN chmod +x /opt/boot.sh

VOLUME ["/etc/haproxy/certs"]

# Run the boot script
CMD /opt/boot.sh
