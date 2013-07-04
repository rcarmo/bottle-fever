#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2013, Rui Carmo
Description: Clustering and statistics helpers
License: MIT (see LICENSE.md for details)
"""

import os, sys, re, logging

log = logging.getLogger()

_stopwords = {"en":"i,a,an,are,as,at,be,by,for,from,how,in,is,it,of,on,or,that,the,this,to,was,what,when,where".split(',')}


def strip_stopwords(sentence, lang="en"):
    """Removes stopwords and normalizes whitespace - adapted from Django"""

    global _stopwords
    words = sentence.split()
    sentence = []
    for word in words:
        if word.lower() not in _stopwords[lang]:
            sentence.append(word)
    return u' '.join(sentence)


def jaccard_distance(a, b):
    """A simple distance function based on string overlap - adapted from sample code by Deepak Thukral"""
    #Tokenize string into bag of words
    feature1 = set(re.findall('\w+', strip_stopwords(a.lower()))[:100])
    feature2 = set(re.findall('\w+', strip_stopwords(b.lower()))[:100])
    similarity = 1.0 * len(feature1.intersection(feature2)) / len(feature1.union(feature2))
    return 1 - similarity



def levenshtein_distance(a, b, limit=None):
    """Returns the Levenshtein edit distance between two strings - adapted from Whoosh"""

    a = ''.join(re.findall('\w+', strip_stopwords(a.lower())))
    b = ''.join(re.findall('\w+', strip_stopwords(b.lower())))

    prev = None
    thisrow = range(1, len(b) + 1) + [0]
    for x in xrange(len(a)):
        # Python lists wrap around for negative indices, so put the
        # leftmost column at the *end* of the list. This matches with
        # the zero-indexed strings and saves extra calculation.
        prev, thisrow = thisrow, [0] * len(b) + [x + 1]
        for y in xrange(len(b)):
            delcost = prev[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = prev[y - 1] + (a[x] != b[y])
            thisrow[y] = min(delcost, addcost, subcost)

        if limit and x > limit and min(thisrow) > limit:
            return limit + 1

    return thisrow[len(b) - 1]


def damerau_levenshtein_distance(a, b, limit=None):
    """Returns the Damerau-Levenshtein edit distance between two strings - adapted from Whoosh"""

    a = ''.join(re.findall('\w+', strip_stopwords(a.lower())))
    b = ''.join(re.findall('\w+', strip_stopwords(b.lower())))

    oneago = None
    thisrow = list(range(1, len(b) + 1)) + [0]
    for x in xrange(len(a)):
        # Python lists wrap around for negative indices, so put the
        # leftmost column at the *end* of the list. This matches with
        # the zero-indexed strings and saves extra calculation.
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(b) + [x + 1]
        for y in xrange(len(b)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (a[x] != b[y])
            thisrow[y] = min(delcost, addcost, subcost)
            # This block deals with transpositions
            if (x > 0 and y > 0 and a[x] == b[y - 1]
                and a[x - 1] == b[y] and a[x] != b[y]):
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)

        if limit and x > limit and min(thisrow) > limit:
            return limit + 1

    return thisrow[len(b) - 1]
