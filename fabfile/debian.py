#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debian/Ubuntu specific tasks

Created by: Rui Carmo
"""

import time
from fabric.contrib.files import contains, exists, cd, append, comment
from fabric.operations import run, sudo, put, hide, settings


def setup_repo(repo):
    if not contains('/etc/apt/trusted.gpg', repo["key_name"], use_sudo=True):
        print("Retrieving repository key %s" % repo["key_url"])
        sudo('/usr/bin/wget --quiet -O - %s | sudo apt-key add -' % repo["key_url"])
    source_list_file = '/etc/apt/sources.list.d/%s.list' % name
    if not exists(source_list_file):
        put(StringIO(repo["source_file"]), source_list_file, use_sudo=True)
        sudo('chmod 0644 %s' % source_list_file)
        sudo('chown root:root %s' % source_list_file)
        print("Repository %s added, updating package list..." % name)
        sudo('apt-get -y update')


def installed(package):
    with settings(warn_only=True):
        return run('dpkg -s %s' % package).succeeded


def install(package):
    if not installed(package):
        with settings(warn_only=True):
            print("Installing %s" % package)
            return sudo('apt-get -y install %s' % package).succeeded


def apt_update(force=False):
    if force or ((time.time() - int(run('stat -t /var/cache/apt/pkgcache.bin').split( )[12])) > 3600*24):
        sudo('apt-get update')


def pip_install(packages):
    if not exists('/usr/local/bin/pip'):
        sudo('/usr/bin/easy_install pip')
    sudo('pip install %s' % ' '.join(packages))
