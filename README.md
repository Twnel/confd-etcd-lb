# confd-etcd-lb

Load balancers backed with confd and etcd.

## Getting Started

Make sure the prerequisites are followed, and the container will be able to run standalone.

### Prerequisites

Docker

```
curl -fsSL get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Installing

Build the app container image locally:

```
docker build --dockerfile <webserver-directory>/Dockerfile -t twnel/<my_image_name> .
```

## Running the tests

After deployment, try: [http:localhost:<standalone port>](http:localhost:<standalone port>)

## Deployment

```
docker run <standalone port>:<container-port> twnel/<my_image_name> .
```

## Built With

* [Nginx](http://nginx.com)
* [confd](http://www.confd.io)
* [etcd](https://coreos.com/etcd/)

## Contributing

1. Create isolated branches for development.
2. Commit your changes, rebase locally from dev/beta branch and create pull requests for the dev/beta branch.
3. Squash merge when approved and delete the alternate remote branch.
4. Rebase the alternate branch locally.
5. Pull requests to higher branches will be done merging the commits, no squash or rebase merge will be done.

## Versioning

For the versions available, see the [tags on this repository](https://github.com/Twnel/confd-etcd-lb/tags). 

## Authors

* **Ericson Cepeda** - *Initial work* - [ericson-cepeda](https://github.com/ericson-cepeda)

See also the list of [contributors](https://github.com/Twnel/confd-etcd-lb/contributors) who participated in this project.

## License

MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* This project contains modifications for Twnel specific requirements.
