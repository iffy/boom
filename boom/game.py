from twisted.internet import reactor
from twisted.internet.defer import Deferred

class Bomb:
    
    def __init__(self, fuse, size):
        self.fuse = fuse
        self.size = size

    def ignite(self):
        d = Deferred()
        reactor.callLater(self.fuse, d.callback, self)
        return d
