# -*- mode: ruby -*-
# vi: set ft=ruby :

# PyBossa Vagrantfile

VAGRANTFILE_API_VERSION = "2"

# Ansible install script for Ubuntu
$ansible_install_script = <<SCRIPT
export DEBIAN_FRONTEND=noninteractive
echo Check if Ansible existing...
if ! which ansible >/dev/null; then
  echo update package index files...
  apt-get update -qq
  echo install Ansible...
  apt-get install -qq ansible
fi
SCRIPT

$ansible_local_provisioning_script = <<SCRIPT
export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
echo PyBossa provisioning with Ansible...
cp /vagrant/provisioning/ansible_hosts /home/vagrant/
chmod 666 /home/vagrant/ansible_hosts
echo Running playbook...
ansible-playbook /vagrant/provisioning/playbook.yml -i /home/vagrant/ansible_hosts -c local
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end
  config.vm.network :forwarded_port, host: 5000, guest: 5000
  config.vm.network :forwarded_port, host: 5001, guest: 5001
  # turn off warning message `stdin: is not a tty error`
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"
  # be sure that there  is Ansible for local provisioning
  config.vm.provision "shell", inline: $ansible_install_script
  # do the final Ansible local provisioning
  config.vm.provision "shell", inline: $ansible_local_provisioning_script
end
