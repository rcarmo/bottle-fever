#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: Utility functions for retrieving CPU statistics
License: MIT (see LICENSE.md for details)
"""

import os, sys, time, logging

log = logging.getLogger()


def stats():
    """Retrieves all CPU counters"""
    cpu = open('/proc/stat','r').readlines()[0]
    return map(float,cpu.split()[1:5])


def usage(interval=0.1):
    """Estimates overall CPU usage during a short time interval"""
    t1 = stats()
    time.sleep(interval)
    t2 = stats() 
    delta = [t2[i] - t1[i] for i in range(len(t1))]
    try:
        return 1.0 - (delta[-1:].pop()/(sum(delta)*1.0))
    except: 
        return 0.0


def freqency(cpu='cpu0'):
    """Retrieves the current CPU speed in MHz - for a single CPU"""
    return float(open('/sys/devices/system/cpu/%s/cpufreq/scaling_cur_freq' % cpu,'r').read().strip())/1000.0


def temperature():
    """Retrieves the current CPU core temperature in degrees Celsius - tailored to the Raspberry Pi"""
    return float(open('/sys/class/thermal/thermal_zone0/temp','r').read().strip())/1000.0
