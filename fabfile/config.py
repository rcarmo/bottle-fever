#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration

Created by: Rui Carmo
"""

paths = {
    "virtualenv": "/srv/bottle-fever/virtualenv"
}


packages = {
    "base"    : ['vim', 'htop', 'tmux', 'wget', 'rsync', 'bash-completion'],
    "postgres": ['postgresql-9.1', 'postgresql-client-9.1', 'libpq-dev'], # stock Ubuntu (Raring)
    "redis"   : ['redis-server'],
    "python"  : ['build-essential', 'python2.7-dev', 'libevent-dev', 'python-setuptools', 'python-virtualenv', 'libxml2-dev', 'libxslt1-dev'],
    "pip"     : [
        "gunicorn==0.17.4",
        "gevent==0.13.8",
        "psycopg2==2.5",
        "Pygments==1.6",
        "celery-with-redis==3.0",
        "nose==1.3.0",
        "flower==0.5.1",
        "whoosh",
        "lxml",
        "bpython"
    ]
}