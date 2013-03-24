#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: Utility functions for retrieving process information
License: MIT (see LICENSE.md for details)
"""

import os, sys, logging, htmlentitydefs

log = logging.getLogger()


def rsplit(s, sep=None, maxsplit=-1):
    """Equivalent to str.split, except splitting from the right"""
    if sys.version_info < (2, 4, 0):
        if sep is not None:
            sep = sep[::-1]
        L = s[::-1].split(sep, maxsplit)
        L.reverse()
        return [s[::-1] for s in L]
    else:
        return s.rsplit(sep, maxsplit)


def shrink(line, bound=50, rep='[...]'):
    """Shrinks a string, adding an ellipsis to the middle"""
    l = len(line)
    if l < bound:
        return line
    if bound <= len(rep):
        return rep
    k = bound - len(rep)
    return line[0:k / 2] + rep + line[-k / 2:]


def convert_entity(m):
    """Converts entities to codepoints where applicable"""
    if m.group(1) == '#':
        try:
            return unichr(int(m.group(2)))
        except ValueError:
            return '&#%s;' % m.group(2)
    try:
        return unichr(htmlentitydefs.name2codepoint[m.group(2)])
    except KeyError:
        return '&%s;' % m.group(2)


def convert_html(buffer):
    """Replaces all entities with codepoints"""
    return re.sub(r'&(#?)(.+?);', convertentity, buffer)


