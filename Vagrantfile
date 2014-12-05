# -*- mode: ruby -*-
# vi: set ft=ruby :

# PyBossas Vagrantfile
# This Vagrantfile requires an additional plugin to work for running Ansible inside the VM.
# Execute on your host once:
#
# vagrant plugin install vagrant-ansible-local
#

VAGRANTFILE_API_VERSION = "2"

# Ansible install script for Ubuntu
$ansible_install_script = <<SCRIPT
if ! which ansible >/dev/null; then
  apt-get update -y
  apt-get install -y ansible
fi
SCRIPT

# Check if vagrant-ansible-local plugin is installed
if !Vagrant.has_plugin?('vagrant-ansible-local')
    puts "The vagrant-ansible-local plugin is missing!"
    puts "Install the plugin with this command and rerun Vagrant:"
    puts
    puts "    vagrant plugin install vagrant-ansible-local"
    puts
    exit 1
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "trusty32"
  config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-i386-vagrant-disk1.box"
  config.vm.network :forwarded_port, host: 5000, guest: 5000
  # be sure that there  is Ansible for local provisioning
  config.vm.provision "shell", inline: $ansible_install_script
  # do the final Ansible *local* provisioning
  config.vm.provision "ansibleLocal" do |ansible|
    ansible.guest_folder = "/vagrant-ansible"
    ansible.raw_arguments = "--inventory=/vagrant-ansible/ansible_hosts"
    ansible.limit = "all"
    ansible.playbook = "provisioning/playbook.yml"
  end
end
