#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery setup

Created by: Rui Carmo
"""


from __future__ import absolute_import

import os, sys
from celery import Celery

sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../lib'))

from config import settings

celery = Celery('tasks.celery',
                broker = settings.celery.broker_url,
                backend = settings.celery.result_backend,
                include=['tasks.workers'])

celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=1000,
    CELERY_ANNOTATIONS = {"tasks.add": {"rate_limit": settings.celery.rate_limit}}
)

if __name__ == '__main__':
    celery.start()
