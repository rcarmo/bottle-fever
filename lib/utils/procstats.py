#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: Utility functions for retrieving process information
License: MIT (see LICENSE.md for details)
"""

import os, sys, logging, platform, __builtin__

log = logging.getLogger()

# Module globals
openfiles = set()
oldfile = __builtin__.file
oldopen = __builtin__.open
patched = False


class _file(oldfile):
    """File wrapper"""
    def __init__(self, *args):
        self.x = args[0]
        log.debug("FILE OPEN: %s" % str(self.x))
        oldfile.__init__(self, *args)
        openfiles.add(self)

    def close(self):
        log.debug("FILE CLOSED: %s" % str(self.x))
        oldfile.close(self)
        openfiles.remove(self)


def _open(*args):
    return newfile(*args)


def monkeypatch_files():
    """Wraps builtin file operations to allow us to track open files"""
    __builtin__.file = _file
    __builtin__.open = _open
    patched = True


def get_open_fd_count():
    if 'Darwin' in platform.platform():
        pid = os.getpid()
        procs = subprocess.check_output([ "lsof", '-w', '-Ff', "-p", str(pid)])
        nprocs = len(filter(lambda s: s and s[0] == 'f' and s[1:].isdigit(),procs.split('\n')))
        return nprocs
    # check if we've monkeypatched anything
    if patched:
        return len(get_open_files())
    else:
        # Will only work for Linux
        return len(os.listdir('/proc/self/fd'))


def get_open_files():
   return [f.x for f in openfiles]


def stats(pid):
    """Retrieve process kernel counters"""
    stats = open('/proc/%d/status' % pid,'r').readlines()
    return dict(filter(lambda x: len(x)==2,map(lambda x: x.split()[:2],stats)))


def rss(pid):
    """Retrieve a process' resident set size"""
    try:
        return int(stats(pid)['VmRSS:'])
    except:
        return 0
