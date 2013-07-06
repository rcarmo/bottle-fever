# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "raring64"

    # config.vm.network :forwarded_port, guest: 80, host: 8080
    config.vm.provision :shell, :inline => <<END
# REMINDER - THESE RUN AS ROOT!
echo "Vagrantfile: shell provisioner started."

# Check if we need to perform a weekly pkgcache update
touch -d '-1 week' /tmp/.limit
if [ /tmp/.limit -nt /var/cache/apt/pkgcache.bin ]; then
    sudo apt-get -y update
fi
rm /tmp/.limit

if [ ! -e /usr/bin/easy_install ]; then
    sudo apt-get -y install python-setuptools
fi

if [ ! -e /usr/local/bin/fab ]; then
    sudo apt-get -y install build-essential python2.7-dev
    sudo easy_install fabric
fi

# generate a dummy keypair for Fabric automation
if [ ! -e ~vagrant/.ssh/id_rsa.pub ]; then 
    sudo -u vagrant ssh-keygen -f ~vagrant/.ssh/id_rsa -t rsa -N ''
    cat ~vagrant/.ssh/id_rsa.pub >> ~vagrant/.ssh/authorized_keys
    chown -R vagrant:vagrant ~vagrant/.ssh
fi

# run Fabric as vagrant user
#if [ -e /vagrant/fabfile ]; then
#    cd /vagrant
#    sudo -u vagrant fab vagrant provision
#fi
echo "Vagrantfile: shell provisioner done."
END
end
