# Original class by Andrew Rowls

from socket import create_connection

class RedisClient(object):
    def __init__(self, host='localhost', port=6379):
        self.sock = create_connection((host, port))
        self.file = self.sock.makefile()

    def __getattr__(self, attr):
        attr = 'del' if attr == 'delete' else attr
        def handle(*args):
            self.sock.send('*%d\r\n' % (len(args)+1))
            [self.sock.send('$%d\r\n%s\r\n' % (len(str(a)), a)) for a in (attr,)+args]
            return self.parse_response()
        return handle

    def parse_response(self):
        rsp = self.file.readline()

        def error(*a): raise Exception(*a)

        type, body = rsp[0], rsp[1:-2]
        return {
            '+': lambda: body,
            '-': lambda: error(body),
            ':': lambda: int(body),
            '$': lambda: self.read_bulk(int(body)),
            '*': lambda: [self.parse_response() for i in range(int(body.splitlines()[0]))],
        }.get(type, lambda: 'Unknown Return Value: "%s"' % body)()

    def read_bulk(self, n):
        return None if n == -1 else self.file.read(n+2)[:-2]


if __name__=='__main__':
    from multiprocessing import Pool
    import time
    import random

    def timed(count):
        c = RedisClient()
        c.select(0)
        seq = range(0,10000)
        for i in seq:
            c.set(random.choice(seq),'bar')
        now = time.time()
        for i in range(0,count):
            c.get(random.choice(seq))
        return time.time() - now

    p = Pool(4)
    print p.map(timed,[10000,10000,10000,10000])
