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

![image](https://user-images.githubusercontent.com/7258463/101060564-8be1e500-355d-11eb-887f-5af65b50ba13.png)

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
additionally to the Manuscript's metadata, the following fields become available:

![image](https://user-images.githubusercontent.com/7258463/101062582-cf3d5300-355f-11eb-93ca-01be71ea04cd.png)
(Paris, F-Pnm lat. 15181)

- The cantus URL
- The cantus CSV export URL, which contains all chant/folio associations for this manuscript

The process for turning any Manuscript in the initialized database into a searchable Manuscript
in the Cantus Ultimus interface involves the following steps:

1. Importing all the chant information of the manuscript
2. Defining the source images of the Manuscript through a IIIF Manifest file
3. Setting the Manuscript as a `public` Manuscript in the Cantus Ultimus interface
4. Map the folio information from Cantus Database to the images obtained from the IIIF Manifest

### Importing chant information

In the admin interface (located in http://localhost:8000/admin), navigate the list of Manuscripts and select the one you wish to enable in Cantus Ultimus.

Select the manuscript by ticking its corresponding check box.

In the `Actions` menu located at the top, trigger the action called `Import the chants associated with the selected manuscript(s)`.

![image](https://user-images.githubusercontent.com/7258463/101063136-79b57600-3560-11eb-97ca-286f1faa06c3.png)

This will trigger a series of queries in the backend. Wait until you see the notification `Loaded chants for manuscript` above the `Actions` menu. It may take a few minutes for this process to complete.

After refreshing the admin page and looking at the Manuscript in the list, it should appear with the flag `Chants loaded` enabled. This indicates that the chant information has been added to the database and solr index. 

![image](https://user-images.githubusercontent.com/7258463/101063628-019b8000-3561-11eb-8609-e986e5002c96.png)

### Defining the source images of the Manuscript through a IIIF Manifest file

Of all the manuscripts in the list displayed in the admin interface, only a handful have a public IIIF Manifest with source images.

IIIF Manifest files can be found within libraries such as [Gallica](https://gallica.bnf.fr/accueil/en/content/accueil-en?mode=desktop), [e-codices](https://www.e-codices.unifr.ch/en), and others.

When a IIIF Manifest is located for a specific manuscript, the URL can be included in the manuscript's metadata.

Click on the Manuscript's entry.

Introduce the IIIF Manifest URL under the `Manifest url` field.

![image](https://user-images.githubusercontent.com/7258463/101063810-41fafe00-3561-11eb-9146-6b4ae1d80b51.png)

Save the changes.

### Setting the Manuscript as a `public` Manuscript in the Cantus Ultimus interface

Making a manuscript a `public` manuscript indicates to the Cantus Ultimus website that the manuscript should show up under the `Manuscript` tab of the final user's web interface.

Click on the Manuscript's entry.

Tick the `public` value.

![image](https://user-images.githubusercontent.com/7258463/101064119-a3bb6800-3561-11eb-9fc0-577d7288c692.png)

Save the changes.

### Map the folio information from Cantus Database to the images obtained from the IIIF Manifest

Once the chant information and IIIF manifest url have been added to a Manuscript, and the manuscript has been marked as `public`, the mapping tool becomes available to map the images with the folio metadata.

The mapping tool is located in the following address: http://localhost:8000/admin/map_folios

Within the mapping tool, the new manuscript should appear with an option to `Map now`.

![image](https://user-images.githubusercontent.com/7258463/101064257-c8174480-3561-11eb-9765-f5207f549ff2.png)

Click on `Map now`.

The mapping tool triggers a heuristic search on the background, which tries to map the images in the IIIF Manifest to the folios described in the Cantus Database.

The result of that automatic process will be displayed in the mapping interface.

At this point, the user might want to verify that the information provided by the automatic mapping is accurate, and correct it when it is not.

In the mapping interface, green folio pages indicate a folio has been mapped to an image manifest, whereas a red folio page indicates that a folio has not been mapped to an image from the manifest.

![image](https://user-images.githubusercontent.com/7258463/101064384-f1d06b80-3561-11eb-8515-570bc99a0b0f.png)

Once the mapping process has been manually revised, conclude the mapping process by clicking on `Submit this Mapping`.

It may take several minutes for the backend of the website to deploy the changes across the database and solr index.

The user will be able to know when that process has concluded by revisiting the admin interface. A complete mapping process will activate the `Is mapped` flag in the corresponding manuscript.

At this point, the manuscript should be searchable within the main website.
