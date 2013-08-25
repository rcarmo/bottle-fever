#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetcher script

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, json, time, logging, logging.config

# Make sure our bundled libraries take precedence
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'lib'))

import config, utils, markup.opml

# read configuration file
config.settings = utils.get_config(os.path.join(utils.path_for('etc'),'config.json'))

# Set up logging
logging.config.dictConfig(dict(config.settings.logging))
log = logging.getLogger()

# load modules
import models, controllers
models.setup()

if __name__ == "__main__":
    log.info("Starting importer.")
     
    fc = controllers.FeedController(config.settings)
    uc = controllers.UserController()
    user = uc.get_user('default')

    feeds = markup.opml.parse_file(sys.argv[1])
    start = time.time()
    for f in feeds:
        feed = fc.add_feed(f['xmlUrl'], title = f['title'], site_url = f['htmlUrl'])
        uc.add_feed_to_group(user, feed, uc.get_group(f['group']))
    log.info("%d feeds imported in %fs" % (len(feeds), time.time() - start))
