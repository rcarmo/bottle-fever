#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generic helpers

Created by: Rui Carmo
"""

from fabric.api import env, local, hosts, roles, shell_env
from fabric.operations import run, sudo, put, hide, settings
from fabric.contrib.files import contains, exists, cd, append, comment
from StringIO import StringIO

def inject_files(files):
    for f in files:
        if not exists(f):
            put(StringIO(files[f]), f, use_sudo = True)
            sudo('chmod 0644 %s' % f)
            sudo('chown root:root %s' % f)


def get_interface_address(intf='eth0'):
    """Obtain the IP address of a given interface on a host"""
    with hide('running','output', 'warnings'):
        return run('/sbin/ifconfig %s | grep "inet addr"' % intf).strip().split('  ')[0].split(':')[1]


def collect_ip_addresses(intf='eth0'):
    """Maintain a local cache of IP addresses"""
    print "Getting IP address for %s" % env.host
    if env.host not in env.addresses:
        env.addresses[env.host] = {}
    if intf not in env.addresses[env.host]:
        env.addresses[env.host][intf] = get_interface_address(intf)


def psql(command):
    """Issue SQL commands to Postgres"""
    if type(command) == list:
        command = '\n'.join(command)
    with hide('running','output', 'warnings'):
        put(StringIO(command),'/tmp/psql.sql', use_sudo = True)
    print "[%s] psql %s" % (env.host,command)
    with hide('running'):
        # workaround for restricted sudo/su environments
        sudo("""bash -c \'su - postgres -s /usr/bin/psql postgres postgres < /tmp/psql.sql\'""")
    with hide('running','output', 'warnings'):
        sudo('rm -f /tmp/psql.sql')