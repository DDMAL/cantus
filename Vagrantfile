# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'vagrant-openstack-provider'

Vagrant.configure(2) do |config|

  config.vm.network :forwarded_port, guest: 8000, host: 8000

  # Solr Port, needed to access admin page
  config.vm.network :forwarded_port, guest: 8983, host: 8080
  config.vm.synced_folder ".", "/vagrant"

  config.vm.provider "virtualbox" do |vb, override|
    override.vm.box = "ubuntu/trusty64"
    vb.customize ["modifyvm", :id, "--ioapic", "on"]
    vb.customize ["modifyvm", :id, "--cpus", "4"]
    vb.customize ["modifyvm", :id, "--memory", "2048"]

    override.vm.provision "shell" do |s|
      s.path = "etc/provision/setup-privileged.sh"
      s.env = {"HOMEUSER" => "vagrant"}
    end
    override.vm.provision "shell" do |s|
      s.privileged = false
      s.path = "etc/provision/setup-unprivileged.sh"
    end
  end

  config.vm.provider "openstack" do |os, override|
    override.ssh.username   = "ubuntu"
    os.openstack_auth_url   = 'https://arbutus.cloud.computecanada.ca:5000/v3'
    os.project_name         = 'rpp-ichiro'
    os.user_domain_name     = "CCDB"
    os.project_domain_name  = 'CCDB'
    os.username             = ENV['CCUSER']
    os.password             = ENV['CCPASSWORD']
    os.region               = 'RegionOne'
    os.flavor               = 'p1-1.5gb'
    os.image                = 'Ubuntu-14.04-trusty-server-cloudimg-amd64'
    os.identity_api_version = '3'
    os.security_groups      = ['Insecure-Group']
    os.floating_ip_pool     = 'Public-Network'

    override.vm.provision "shell" do |s|
      s.path = "etc/provision/setup-privileged.sh"
      s.env = {"HOMEUSER" => "ubuntu"}
    end
    override.vm.provision "shell" do |s|
      s.privileged = false
      s.path = "etc/provision/setup-unprivileged.sh"
    end
  end

end
