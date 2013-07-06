#!/usr/bin/env python
# encoding: utf-8
"""
Haystack.py

An on-disk cache with a dict-like API,inspired by Facebook's Haystack store

Created by Rui Carmo on 2010-04-05
Published under the MIT license.
"""
__author__ = ('Rui Carmo http://the.taoofmac.com')
__revision__ = "$Id$"
__version__ = "1.0"

import os, sys, stat, mmap, thread, time, logging

log = logging.getLogger()

try:
    import cPickle as pickle
except ImportError:
    import pickle # fall back on Python version

class Haystack(dict):

    def __init__(self,path,basename = "haystack", commit = 300, compact = 3600):
        super(Haystack,self).__init__()
        self.enabled = True
        self.mutex = thread.allocate_lock()
        self.commitinterval = commit
        self.compactinterval = compact
        self.path = path
        self.basename = basename
        self.cache = os.path.join(self.path,self.basename + '.bin')
        self.index = os.path.join(self.path,self.basename + '.idx')
        self.temp = os.path.join(self.path,self.basename + '.tmp')   
        self._rebuild()
        self.created = self.modified = self.compacted = self.committed = time.time()
  

    def _rebuild(self):
        self.mutex.acquire()
        try:
            os.makedirs(self.path)
        except Exception, e:
            log.error("Error on makedirs(%s): %s" % (self.path, e))
            pass
        try:
            cache = open(self.cache,"rb")
        except Exception, e:
            log.error("Error while opening %s for reading: %s" % (self.cache, e))
            cache = open(self.cache,"ab")
        cache.close()
        try:
            self._index = pickle.loads(open(self.index,"rb").read())
        except Exception, e:
            log.error("index retrieval from disk failed: %s" % e)
            self._index = {} # "key": [mtime,length,offset]
        self.created = self.modified = self.compacted = self.committed = time.time()
        log.debug("Rebuild complete, %d items." % len(self._index.keys()))
        self.mutex.release()
  

    def commit(self):
        if not self.enabled:
            return
        self.mutex.acquire()
        open(self.index,"wb").write(pickle.dumps(self._index))
        self.committed = time.time()
        log.debug("Index %s commited, %d items." % (self.index, len(self._index.keys())))
        self.mutex.release()


    def purge(self):
        self.mutex.acquire()
        try:
            os.unlink(self.index)
        except OSError, e:
            log.error("Could not unlink %s: %s" % (self.index, e))
            pass
        try:
            os.unlink(self.cache)
        except OSError, e:
            log.error("Could not unlink %s: %s" % (self.index, e))
            pass
        self.mutex.release()
        self._rebuild()


    def _cleanup(self):
        now = time.time()
        if now > (self.committed + self.commitinterval):
            self.commit()
        if now > (self.compacted + self.compactinterval):
            self._compact()
    

    def __eq__(self,other):
        raise TypeError('Equality undefined for this kind of dictionary')
  

    def __ne__(self,other):
        raise TypeError('Equality undefined for this kind of dictionary')
  

    def __lt__(self,other):
        raise TypeError('Comparison undefined for this kind of dictionary')
  

    def __le__(self,other):
        raise TypeError('Comparison undefined for this kind of dictionary')
  

    def __gt__(self,other):
        raise TypeError('Comparison undefined for this kind of dictionary')
  

    def __ge__(self,other):
        raise TypeError('Comparison undefined for this kind of dictionary')
  

    def __repr__(self,other):
        raise TypeError('Comparison undefined for this kind of dictionary')
  

    def expire(self,when):
        """Remove from cache any items older than a specified time"""
        if not self.enabled: return
        self.mutex.acquire()
        for k in self._index.keys():
            if self._index[k][0] < when:
                del self._index[k]
        self.mutex.release()
        self._cleanup()
  

    def keys(self):
        return self._index.keys()
      

    def stats(self,key):
        if not self.enabled:
            raise KeyError
        self.mutex.acquire()
        try:
            stats = self._index[key]
            self.mutex.release()
            return stats
        except KeyError:
            self.mutex.release()
            raise KeyError
  

    def __setitem__(self,key,val):
        """Store an item in the cache - errors will cause the entire cache to be rebuilt"""
        if not self.enabled:
            return
        self.mutex.acquire()
        try:
            cache = open(self.cache,"ab")
            buffer = pickle.dumps(val,2)
            offset = cache.tell()
            cache.write(buffer)
            self.modified = mtime = time.time()
            self._index[key] = [mtime,len(buffer),offset]
            cache.flush()
            cache.close()
            self.mutex.release()
        except Exception, e:
            log.error("Error while storing %s: %s" % (key, e))
            self.mutex.release()
            raise IOError
    

    def __delitem__(self,key):
        """Remove item from cache - in practice, we only remove it from the index"""
        if not self.enabled:
            return
        self.mutex.acquire()
        try:
            del self._index[key]
            self.mutex.release()    
        except Exception, e:
            log.error("Error while deleting %s: %s" % (key, e))
            self.mutex.release()    
            raise KeyError
  

    def get(self,key,default):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


    def __getitem__(self,key):
        """Retrieve item"""
        if not self.enabled:
            raise KeyError
        self.mutex.acquire()
        try:
            cache = open(self.cache,"rb")
            cache.seek(self._index[key][2])
            buffer = cache.read(self._index[key][1])
            item = pickle.loads(buffer)
            self.mutex.release()
        except Exception, e:
            log.error("Error while retrieving %s: %s" % (key, e))
            self.mutex.release()
            raise KeyError  
        finally:
            cache.close()
        return item
  

    def mtime(self,key):
        """Return the creation/modification time of a cache item"""
        if not self.enabled:
            raise KeyError
        self.mutex.acquire()
        try:
            item = self._index[key][0]
            self.mutex.release()
            return item
        except Exception, e:
            log.debug("Error while getting modification time for %s: %s" % (key, e))
            self.mutex.release()
            raise KeyError
        

    def _compact(self):
        """Compact the cache"""
        self.mutex.acquire()
        cache = open(self.cache,"rb")
        compacted = open(self.temp,"ab")
        newindex = {}
        i = 0
        for key in self._index.keys():
            cache.seek(self._index[key][2])
            offset = compacted.tell()
            compacted.write(cache.read(self._index[key][1]))
            newindex[key] = [time.time(),self._index[key][1],offset]
            i = i + 1
        cache.close()
        size = compacted.tell()
        compacted.flush()
        os.fsync(compacted.fileno())
        compacted.close()
        os.rename(self.temp,self.cache)
        self.compacted = time.time()
        self._index = newindex
        self.mutex.release()
        self.commit()
        log.debug("Compacted %s: %d items into %d bytes" % (self.cache, i, size))


if __name__=="__main__":
    c = Haystack('.', commit = 3, compact = 4)
    c['tired'] = "to expire in 2 seconds"
    for i in range(1,10):
        time.sleep(1)
        c['foo'] = {'a':1}
        c['zbr'] = '42'
        c['test/path/name'] = "test"
        c.expire(time.time() - 2)
        del c['foo']
        assert(c['zbr']=='42') # will eventually fail with KeyError when the cache times out

