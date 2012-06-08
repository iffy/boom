from twisted.internet import reactor
from twisted.internet.defer import Deferred

EMPTY = 0
HARD = 1
SOFT = 2


class Board:
    """
    The board is made of 3 layers:
        
        1. Background: Tiles are all the same currently.  In the
           future, if things like conveyor belts or wormholes are
           to be supported, they will appear in this layer.

        2. Foreground: Tiles are either EMPTY, HARD or SOFT
        
        3. Players/bombs/items: Tiles may have one or more of the
           moveable things on it (players, bombs, powerups).

    XXX vars
    """


    def __init__(self, reactor=reactor):
        self.fg_tiles = {}
        self.bombs = {}
        self.fires = {}
        self._reactor = reactor


    def generate(self, width, height):
        """
        XXX
        """
        for x in xrange(width):
            for y in xrange(height):
                coord = (x,y)
                if (x % 2) and (y % 2):
                    self.fg_tiles[coord] = HARD
                else:
                    self.fg_tiles[coord] = SOFT


    def fgTile(self, coord):
        """
        XXX
        """
        return self.fg_tiles[coord]


    def dropBomb(self, coord, fuse, size):
        """
        XXX
        """
        defer = Deferred()
        self._reactor.callLater(fuse, defer.callback, None)
        self.bombs[coord] = defer
        
        # remove bomb after it explodes
        def rmBomb(r, board, coord):
            del board.bombs[coord]
            return r
        defer.addCallback(rmBomb, self, coord)

        return defer


    def stopFire(self, coord):
        """
        XXX
        """
        d, call = self.fires[coord]
        d.callback(None)
        del self.fires[coord]


    def startFire(self, coord, burntime):
        """
        XXX
        """
        if coord in self.fires:
            defer, call = self.fires[coord]
            call.delay(burntime)
        else:
            defer = Deferred()
            call = self._reactor.callLater(burntime, 
                                           self.stopFire, 
                                           coord)
            self.fires[coord] = (defer, call)
            self.fg_tiles[coord] = EMPTY
        return defer



class Bomb:
    
    def __init__(self, fuse, size):
        self.fuse = fuse
        self.size = size

    def ignite(self):
        d = Deferred()
        reactor.callLater(self.fuse, d.callback, self)
        return d
