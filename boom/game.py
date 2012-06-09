"""
Board and players and such.

@var EMPTY: signifies an empty tile
@var HARD: signifies a tile which can not be blown up
@var SOFT: signifies a tile which can be blown up
"""
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


    @ivar bombs: Dictionary whose keys are coordinate tuples
        and whose values are an implementation detail.  You are
        welcome to see if a bomb is present by testing coordinates
        in this dict.
    
    @ivar fires: Dictionary whose keys are coordinate tuples.
        If the tuple is there, the fire is there, though you 
        shouldn't mess with the value.
    
    @ivar fg_tiles: Dictionary of foreground tiles.  Keys are
        coordinate tuples.
    
    @ivar dft_burn: Number of seconds flames last by default.
    """
    
    dft_burn = 1


    def __init__(self, reactor=reactor):
        self.fg_tiles = {}
        self.bombs = {}
        self.fires = {}
        self._reactor = reactor


    def generate(self, width, height):
        """
        Generate a standard board.
        
        @param width: Number of tiles wide the board will be
        @param height: Number of tiles high the board will be
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
        Get the tile at the given location.
        
        @param coord: Coordinate tuple.
        
        @return: C{EMPTY}, C{HARD} or C{SOFT} (from this module)
        """
        return self.fg_tiles[coord]


    def dropBomb(self, coord, fuse, size):
        """
        Place a bomb on the board, and ignite it.
        
        @param coord: Coordinate tuple where the bomb will go.
        
        @type fuse: int or float
        @param fuse: Number of seconds until the bomb explodes
        
        @type size: int
        @param size: Size of explosion (number of adjacent tiles
            affected)
        
        @return: A L{Deferred} that will fire when the bomb 
            explodes.
        """
        defer = Deferred()
        self._reactor.callLater(fuse, defer.callback, None)
        self.bombs[coord] = (defer, size)
        
        # remove bomb after it explodes
        def rmBomb(r, board, coord):
            board.detonateBomb(coord)
            return r
        defer.addCallback(rmBomb, self, coord)

        return defer


    def detonateBomb(self, coord):
        """
        XXX
        """
        defer, size = self.bombs[coord]
        del self.bombs[coord]
        
        # we did start the fire
        self.startFire(coord, self.dft_burn)
        # up
        directions = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0),
        ]
        for i in xrange(1, size+1):
            for d in list(directions):
                target = (coord[0]+(d[0]*i), coord[1]+(d[1]*i))
                try:
                    tile = self.fg_tiles[target]
                except KeyError:
                    continue
                if tile == HARD:
                    directions.remove(d)
                    continue
                self.startFire(target, self.dft_burn)


    def stopFire(self, coord):
        """
        Put out a fire and notify listening people via the 
        L{Deferred}.  Used internally by L{startFire}, but maybe
        we'll let people put out fires with some power.
        
        @param coord: Coordinate tuple where fire is
        """
        d, call = self.fires[coord]
        d.callback(None)
        del self.fires[coord]


    def startFire(self, coord, burntime):
        """
        Start a fire on a tile.  Normally, this will happen as a
        natural effect of lighting a bomb.  But, hey, let people
        light fires if they want, eh?
        
        If you start a new fire on a currently burning tile, the
        conflagration will continue until the end of the most 
        recent ignition.
        
        XXX if we start a 10 second fire, then start a 1 second
        fire 1 second later, it should burn through the 10 seconds.
        
        @param coord: Coordinate tuple to ignite
        
        @type burntime: int or float
        @param burntime: Seconds to keep burning.
        
        @return: L{Deferred} which fires when the fire is out.
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
