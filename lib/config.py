#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: Shared configuration data
License: MIT (see LICENSE.md for details)
"""

import os, sys, logging.config
from utils import get_config

try:
    settings
except NameError:
    settings = get_config(os.path.join(os.path.dirname(__file__),'..','etc','config.json'))
    logging.config.dictConfig(dict(settings.logging))
