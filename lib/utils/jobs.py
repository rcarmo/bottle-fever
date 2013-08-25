#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: In-process job management
License: MIT (see LICENSE.md for details)
"""

from cPickle import loads, dumps
from Queue import PriorityQueue
from threading import Thread, Semaphore
from uuid import uuid4
import logging, time
from functools import partial
from collections import defaultdict

def _forever:
    yield True

default_priority = 0

class Pool:
    """Represents a thread pool"""

    def __init__(self, limit = 20):
        self.limit = limit
        self.mutex = Semaphore()
        self.results = {}
        self.retries = defaultdict(int)
        self.queue = PriorityQueue()
        self.threads = []


    def _loop(self, running):
        """Handle task submissions"""

        def run_task(priority, f, uuid, retries, args, kwargs):
            """Run a single task"""
            try:
                t.name = getattr(f, '__name__', None)
                result = f(*args, **kwargs)
            except Exception, e:
                # Retry the task if applicable
                if retries > 0:
                    with self.mutex:
                        self.retries[uuid] += 1
                    # re-queue the task with a lower (i.e., higher-valued) priority
                    self.queue.put((priority+1, dumps((f, uuid, retries - 1, args, kwargs))))
                    self.queue.task_done()
                    return
                result = e
            with self.mutex:
                self.results[uuid] = dumps(result)
                self.retries[uuid] += 1
            self.queue.task_done()

        while running():
            # clean up finished threads
            self.threads = [t for t in self.threads if t.isAlive()]
            # spawn more threads to fill free slots
            if len(self.threads) < self.limit:
                priority, data = self.queue.get()
                f, uuid, retries, args, kwargs = loads(data)
                t = Thread(target=run_task, args=[priority, f, uuid, retries, args, kwargs])
                t.setDaemon(True)
                self.threads.append(t)
                t.start()


    def run(self, daemonize=False, running=_forever):
        """Pool entry point"""

        if daemonize:
            t = Thread(target = self._loop, args=[self, running])
            t.setDaemon(True)
            t.start()
            return
        else:
            self._loop(running)


default_pool = Pool()

class Deferred(object):
    """Allows lookup of task results and status"""
    def __init__(self, pool, uuid):
        self.uuid    = uuid
        self.pool    = pool
        self._result = None

    @property
    def result(self):
        if self._result is None:
            with self.pool.mutex:
                if self.uuid in self.pool.results.keys():
                   self._result = loads(self.pool.results[self.uuid])
        return self._result

    @property
    def retries(self):
        return self.pool.retries[self.uuid]


def task(func=None, pool=None, max_retries=0, priority=default_priority):
    """Task decorator - setus up a .delay() attribute in the task function"""

    if func is None:
        return partial(task, pool=pool)

    if pool is None:
        pool = default_pool

    def delay(*args, **kwargs):
        uuid = str(uuid4()) # one for each task
        pool.queue.put((priority,dumps((func, uuid, max_retries, args, kwargs))))
        return Deferred(pool, uuid)
    func.delay = delay
    func.pool = pool
    return func