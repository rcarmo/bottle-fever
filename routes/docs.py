#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API documentation handler

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging
from bottle import route, view

log = logging.getLogger()

import utils

@route('/docs/<path:path>')
@view('docs.tpl')
def send_doc_wrapper(path):
    """Render documentation for a specific API module"""
    docs = utils.docs()
    if path in docs:
        return {"title": path.title(), "docs": docs[path]}
    abort(404,"Not Found")
