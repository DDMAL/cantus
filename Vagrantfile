# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.network :forwarded_port, guest: 8000, host: 8000
  config.vm.network :forwarded_port, guest: 22, host: 2223, id: "ssh"

  # Solr Port, needed to access admin page
  config.vm.network :forwarded_port, guest: 8983, host: 8080

  config.vm.provision "shell", path: "etc/provision/setup.sh"

  config.vm.provision "shell", privileged: false, path: "etc/provision/setup-unprivileged.sh"

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--ioapic", "on"]
    vb.customize ["modifyvm", :id, "--cpus", "4"]
    vb.customize ["modifyvm", :id, "--memory", "2048"]
  end
end
