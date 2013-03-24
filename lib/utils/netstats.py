#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2013, Rui Carmo
Description: Network utility functions
License: MIT (see LICENSE.md for details)
"""

import os, sys, time, re, logging
import socket, struct

log = logging.getLogger()


def valid_mac_address(addr):
    """Validate a physical Ethernet address"""
    return re.match("[0-9a-f]{2}([-:][0-9a-f]{2}){5}$", addr.lower())


def valid_ip_address(addr):
    """Quick and dirty way to validate any kind of IP address"""
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False


def get_net_bytes(dev='eth0'):
    """Read network interface traffic counters"""
    return {
        'rx': float(open('/sys/class/net/%s/statistics/rx_bytes' % dev,'r').read().strip()),
        'tx': float(open('/sys/class/net/%s/statistics/tx_bytes' % dev,'r').read().strip())
    }


def get_mac_address(dev="eth0"):
    """Retrieves the MAC address from the /sys virtual filesystem - will only work on Linux."""
    return open('/sys/class/net/%s/address' % dev,'r').read().strip()


def get_ip_address(dev="eth0"):
    """Retrieves the IP address via SIOCGIFADDR - only tested on Linux."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', dev[:15]))[20:24])
    except:
        return None