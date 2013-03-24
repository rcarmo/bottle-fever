#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetcher script

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, json, multiprocessing, logging, logging.config

# Make sure our bundled libraries take precedence
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))

import config, utils, opml

# read configuration file
config.settings = utils.get_config(os.path.join(utils.path_for('data'),'config.json'))

# Set up logging
logging.config.dictConfig(dict(config.settings.logging))
log = logging.getLogger()

# load modules
import models, controllers
models.setup()

if __name__ == "__main__":
    log.info("Starting fetcher.")
        
    fc = controllers.FeedController()
    p = multiprocessing.Pool(processes=8)
    p.map(controllers.feed_worker, fc.get_feeds(), 10)
    #for f in fc.get_feeds():
    #    controllers.feed_worker(f)
