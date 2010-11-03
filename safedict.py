import thread
from contextlib import contextmanager
from collections import MutableMapping

class RWLock(object):

    def __init__(self):
        self.wrtlock = thread.allocate_lock()
        self.mutex = thread.allocate_lock()
        self.rdcount = 0

    @contextmanager
    def write(self):
        with self.wrtlock:
            yield

    @contextmanager
    def read(self):
        with self.mutex:
            self.rdcount += 1
            if self.rdcount == 1: self.wrtlock.acquire()
        yield
        with self.mutex:
            self.rdcount -= 1
            if self.rdcount == 0: self.wrtlock.release()

class ThreadSafeDict(MutableMapping):

    def __init__(self, *args, **kwargs):
        self.__d = dict(*args, **kwargs)
        self.__l = RWLock()

    def __contains__(self, b):
        with self.__l.read():
            return b in self.__d

    def __len__(self):
        with self.__l.read():
            return len(self.__d)

    def __iter__(self):
        with self.__l.read():
            for k in self.__d:
                yield k

    def __getitem__(self, key):
        with self.__l.read():
            return self.__d[key]

    def __delitem__(self, key):
        with self.__l.write():
            del self.__d[key]

    def __setitem__(self, key, value):
        with self.__l.write():
            self.__d[key] = value
