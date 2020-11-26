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

### Launch in development (Vagrant + Virtualbox)

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

### Launch in production (Vagrant + OpenStack)

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

## Initialize a newly launched website

A freshly initialized instance of the website does not have an admin account. Addititionally, the database of Manuscripts, Chants, and Folios is not populated.

A few commands will create an admin account and populate the database.

Assuming that the site has been launched and is accessible in http://localhost:8000/, fire up another terminal and `ssh` into the server.

```sh
# SSH into the VM
$ vagrant ssh
# Go to the public folder in the VM
[vagrant]$ cd public
# Activate the Python virtualenv
[vagrant]$ source app_env/bin/activate
```

The first thing we need to do is to create an admin account for the website.

```sh
# Creating a django admin account for the website
[vagrant](app_env)$ python manage.py createsuperuser

Username (leave blank to use 'vagrant'): 
Email address: 
Password: 
Password (again): 
Superuser created successfully.
```

Using your admin credentials, verify that you are able to log into the admin django site, which should be located in http://localhost:8000/admin/

When navigating through any of the tables in the admin interface (e.g., Manuscripts, Concordances, and Chants), they will appear to be empty.

We can pre-populate the Concordances, Manuscripts, and Chants from the information available in the [Cantus Database](http://cantus.uwaterloo.ca/).

The scripts to populate the database are included in the repository. Head back to the terminal where you created the admin user account.

Import the concordances, manuscripts, and chants

```sh
# Import the concordances
[vagrant](app_env)$ python manage.py import_data concordances
Deleting old concordances data...
Successfully imported 12 concordances into database.
Waiting for Solr to finish...
Done.

# Import the manuscripts
[vagrant](app_env)$ python manage.py import_data manuscripts
Deleting old manuscripts data...
Starting manuscript import process.
# It should take about 5 minutes to import the data.
Successfully imported 155 manuscripts into database.
Waiting for Solr to finish...
Done.
```

An additional command is included to import chants associated with a specific manuscript

```sh
[vagrant](app_env)$ python manage.py import_data chants --manuscript-id MANUSCRIPT_ID
```
however, this process can already be done using the user interface. We recommend using the user interface from this point onward.

## Adding manuscripts and chants using the admin user interface

Once the manuscript information has been fetched from the Cantus Database,
the following fields of a manuscript should become available:

- The cantus URL
- The cantus CSV export URL, which contains all chant/folio associations for this manuscript

The process for turning any Manuscript in the initialized database into a searchable Manuscript
in the Cantus Ultimus interface involves the following steps:

1. Importing all the chant information of the manuscript
2. Defining the source images of the Manuscript through a IIIF Manifest file
3. Setting the Manuscript as a `public` Manuscript in the Cantus Ultimus interface

### Importing chant information

In the admin interface (located in http://localhost:8000/admin), navigate the list of Manuscripts and select the one you wish to enable in Cantus Ultimus.

Select the manuscript by ticking its corresponding check box.

In the `Actions` menu located at the top, trigger the action called `Import the chants associated with the selected manuscript(s)`.

This will trigger a series of queries in the backend. Wait until you see the notification `Loaded chants for manuscript` above the `Actions` menu. It may take a few minutes for this process to complete.

After refreshing the admin page and looking at the Manuscript in the list, it should appear with the flag `Chants loaded` enabled. This indicates that the chant information has been added to the database and solr index. 

