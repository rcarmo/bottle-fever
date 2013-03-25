#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetcher script

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, time, json, logging, logging.config

# Make sure our bundled libraries take precedence
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))

import config, utils

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
    start = time.time()
    fc = controllers.FeedController()
    feeds = fc.get_feeds()
    if config.settings.fetcher.pool:
        if config.settings.fetcher.engine == 'multiprocessing':
            from multiprocessing import Pool
            p = Pool(processes=config.settings.fetcher.pool)
            p.map(controllers.feed_worker, feeds, len(feeds)/config.settings.fetcher.pool)
        elif config.settings.fetcher.engine == 'gevent':
            from gevent import monkey; monkey.patch_all()
            from gevent.pool import Pool
            p = Pool(config.settings.fetcher.pool)
            run = [g for g in p.imap_unordered(controllers.feed_worker, feeds)]
    else:
        for f in feeds:
            controllers.feed_worker(f)
    log.info("%d feeds handled in %fs" % (len(feeds), time.time() - start))

