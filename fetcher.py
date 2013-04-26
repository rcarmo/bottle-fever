#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetcher script

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, time, json, logging, logging.config, itertools

# Make sure our bundled libraries take precedence
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))

import config, utils

# read configuration file
config.settings = utils.get_config(os.path.join(utils.path_for('etc'),'config.json'))

# Set up logging
logging.config.dictConfig(dict(config.settings.logging))
log = logging.getLogger()

# load modules
import models, controllers
models.setup()
models.setup_index()

def grouper(n, iterable):
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk

def chunk_wrapper(feeds):
     from gevent import monkey; monkey.patch_all()
     from gevent.pool import Pool
     p = Pool(config.settings.fetcher.mix_pool)
     log.info(">> starting %d greenlets" % config.settings.fetcher.mix_pool)
     p.map(controllers.feed_worker, feeds)

if __name__ == "__main__":
    log.info("Starting fetcher.")
    start = time.time()
    fc = controllers.FeedController()
    feeds = fc.get_feeds(all=True)
    if config.settings.fetcher.pool:
        # multiple processes
        if config.settings.fetcher.engine == 'multiprocessing':
            from multiprocessing import Pool
            p = Pool(processes=config.settings.fetcher.pool)
            log.info(">> starting %d workers" % config.settings.fetcher.pool)
            p.map(controllers.feed_worker, feeds, config.settings.fetcher.chunk_size)
        # multiple greenlets
        elif config.settings.fetcher.engine == 'gevent':
            from gevent import monkey; monkey.patch_all()
            from gevent.pool import Pool
            p = Pool(config.settings.fetcher.pool)
            log.info(">> starting %d greenlets" % config.settings.fetcher.pool)
            run = [g for g in p.imap_unordered(controllers.feed_worker, feeds)]
        # multiple processes with greenlets (FFA mode)
        elif config.settings.fetcher.engine == 'mixed':
            from multiprocessing import Pool
            p = Pool(processes=config.settings.fetcher.pool)
            log.info(">> starting %d workers" % config.settings.fetcher.pool)
            p.map(chunk_wrapper, grouper(config.settings.fetcher.chunk_size,feeds))
    else:
        for f in feeds:
            controllers.feed_worker(f)
    log.info("%d feeds handled in %fs" % (len(feeds), time.time() - start))

