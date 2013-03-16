#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main application script

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, json, logging, logging.config

# Make sure our bundled libraries take precedence
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))

import bottle, utils

# read configuration file
config = utils.get_config(os.path.join(utils.path_for('data'),'config.json'))

# Set up logging
logging.config.dictConfig(dict(config.logging))
log = logging.getLogger()

if __name__ == "__main__":

    if config.debug:
        if 'BOTTLE_CHILD' not in os.environ:
            log.debug('Using reloader, spawning first child.')
        else:
            log.debug('Child spawned.')

    if not config.debug or ('BOTTLE_CHILD' in os.environ):
        log.info("Setting up application.")
        import api, routes, controllers
        log.info("Serving requests.")

    bottle.run(
        port     = config.http.port, 
        host     = config.http.bind_address, 
        debug    = config.debug,
        reloader = config.debug
    )
