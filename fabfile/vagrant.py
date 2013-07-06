#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vagrant-specific tooling

Created by: Rui Carmo
"""

def vagrant():
    """Allow fabric to manage a Vagrant VM/LXC container"""
    env.user = 'vagrant'
    with hide('running','output'):
        v = dict(map(lambda l: l.strip().split(),local('vagrant ssh-config', capture=True).split('\n')))
    # Build a valid host entry
    env.hosts = ["%s:%s" % (v['HostName'],v['Port'])]
    # Use Vagrant SSH key
    if v['IdentityFile'][0] == '"':
        env.key_filename = v['IdentityFile'][1:-1]
    else:
        env.key_filename = v['IdentityFile']
