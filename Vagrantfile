# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "raring64"

    # config.vm.network :forwarded_port, guest: 80, host: 8080
    config.vm.provision :shell, :inline => <<END
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
    sudo apt-get -y install build-essential python-dev 
    sudo easy_install fabric
fi

echo "Checking for fabfile..."
if [ -e /vagrant/fabfile ]; then
    cd /vagrant
    fab provision
fi
echo "Done."
END
end
