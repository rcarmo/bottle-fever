#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debugging routes

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""
import os, sys, logging, cgi

log = logging.getLogger()

from bottle import app, route, request

@route('/headers')
def dump_headers():
    """Dump headers for debugging"""
    result = ["%s: %s" % (x, request.headers[x]) for x in request.headers.keys()]
    result.append('\n')
    return "<pre>%s</pre>" % cgi.escape('\n'.join(result))
    
