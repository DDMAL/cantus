# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty32"

  config.vm.network :forwarded_port, guest: 8000, host: 8000
  config.vm.network :forwarded_port, guest: 22, host: 2223, id: "ssh"

  config.vm.provision "shell", path: "etc/provision/setup.sh", args: ["/vagrant"]

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end
end
