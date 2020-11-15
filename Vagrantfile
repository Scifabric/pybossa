# -*- mode: ruby -*-
# vi: set ft=ruby :

# PYBOSSA Vagrantfile

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "bento/ubuntu-20.04"
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end
  config.vm.network :forwarded_port, host: 5000, guest: 5000
  config.vm.network :forwarded_port, host: 5001, guest: 5001
  # turn off warning message `stdin: is not a tty error`
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"
  config.vm.provision "shell", path: "contrib/server.sh"
  config.vm.provision "shell", path: "contrib/pybossa.sh", privileged: false
end
