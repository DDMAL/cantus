# [Cantus Ultimus](http://cantus.simssa.ca/)

[![Build Status](https://travis-ci.org/DDMAL/cantus.svg?branch=develop)](https://travis-ci.org/DDMAL/cantus) [![Coverage Status](https://coveralls.io/repos/github/DDMAL/cantus/badge.svg?branch=develop)](https://coveralls.io/github/DDMAL/cantus?branch=develop)

Serving images on a website using [Apache Solr](http://lucene.apache.org/solr/), [Diva.js](https://ddmal.github.io/diva.js/) and the [CANTUS](http://cantusdatabase.org/) collection.

## Cloning the repository

The repository of the Cantus Ultimus website has a submodule `cantus-staticpages` with the static pages of the website.

Therefore, when cloning the repository, please add the `--recursive` flag:

```
git clone https://github.com/DDMAL/cantus.git --recursive
```

An alternative option is to clone the repository as you normally would, and then get the submodule:

```
git submodule update --init
```

## Launching the website
The easiest way to launch an instance of the website is to run a virtual machine using [Vagrant](https://www.vagrantup.com/). It should also be possible (with some work) to set up the development server directly in a Unix-like environment.

For simplicity, we assume that you will be running the site using [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/) as a provider, and that both are installed in your local machine. 

For deploying in production or using a different provider (e.g., OpenStack inside ComputeCanada) an external provider plugin may be necessary. In our case, we require [vagrant-openstack-provider](https://github.com/ggiamarchi/vagrant-openstack-provider) to deploy in a remote [OpenStack](https://www.openstack.org/) cloud.

## Launch in development (Vagrant + Virtualbox)

With Vagrant, execute the following commands from the root directory of the repo:

```sh
# The openstack plugin will be needed to deploy in production
$ vagrant plugin install vagrant-openstack-provider

# Set up the VM (this will take a while)
$ vagrant up

# SSH into the VM
$ vagrant ssh

# Go to the public folder in the VM
[vagrant]$ cd public

# Activate the Python virtualenv
[vagrant]$ source app_env/bin/activate

# Run the server on 0.0.0.0 to expose it outside of the VM
[vagrant](app_env)$ python manage.py runserver 0.0.0.0:8000
```

The site should now be accessible on http://localhost:8000/ in your host machine.

## Launch in production (Vagrant + OpenStack)

The OpenStack provider we are using is on a remote cloud. The credentials for accessing that cloud must be set before launching the instance:

```sh
$ export CCUSER YOUR_USERNAME
$ export CCPASSWORD YOUR_PASSWORD

$ vagrant up --provider openstack
```

If the connection to the provider was successful, `vagrant ssh` should provide access to the remote VM.
```sh
# SSH into the VM
$ vagrant ssh
```