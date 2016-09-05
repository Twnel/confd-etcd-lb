docker build -t twnel/nginx-sky:dev .

docker rm -f nginx
source /etc/environment;
docker run --rm --name nginx -p 443:443 -p 80:80 --net host \
-v /home/core/apn_cert/certs/:/etc/nginx/certs/ --privileged=true -e CLUSTER=beta \
-e DOMAIN=twnel.me -e REGION=api -e HTPASSWD=$(etcdctl get /nginx/pwd) twnel/nginx-sky:dev
docker logs nginx
