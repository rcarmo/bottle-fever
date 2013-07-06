#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main fabric module

Created by: Rui Carmo
"""

import os, sys, time, logging
from fabric.api import env, local, hosts, roles, execute, task, prefix
from fabric.operations import run, sudo, put, hide, settings
from fabric.contrib.files import contains, exists, cd, append, comment
from fabric.contrib.project import rsync_project
from StringIO import StringIO

from .config import packages, paths
from .debian import install, pip_install
from contextlib import contextmanager

@contextmanager
def virtualenv(path):
    with cd(path):
        with prefix('source ' + os.path.join(path,'bin','activate')):
            yield

@task
def vagrant():
    env.user  = 'vagrant'
    env.hosts = ['localhost']

def test():
    local("nosetests")


def setup_database():
    """Create the echoprint database and associated user with a temporary password"""
    with hide('output', 'running'):
        with settings(warn_only=True):
            psql("CREATE USER vagrant;")
        with settings(warn_only=True):
            psql("CREATE DATABASE feeds;")
        psql("GRANT ALL ON DATABASE feeds TO vagrant;")


@task
def provision():
    with hide('running','output','warnings'):
        map(install,packages['base'])
        map(install,packages['postgres'])
        map(install,packages['redis'])
        map(install,packages['python'])

        if not exists(paths['virtualenv']):
            sudo('mkdir -p %s' % paths['virtualenv'])
            sudo('virtualenv %s' % paths['virtualenv'])
            sudo('chown -R www-data:www-data %s' % paths['virtualenv'])
        with virtualenv(paths['virtualenv']):
            pip_install(packages['pip'])
