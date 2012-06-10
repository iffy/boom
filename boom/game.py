"""
Board and players and such.

@var EMPTY: signifies an empty tile
@var HARD: signifies a tile which can not be blown up
@var SOFT: signifies a tile which can be blown up
"""
from twisted.internet import reactor
from twisted.internet.defer import Deferred

import time

EMPTY = 0
HARD = 1
SOFT = 2


class YoureDead(Exception): pass
class IllegalMove(Exception): pass


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
    
    @ivar pawns: C{set} of L{Pawns<Pawn>} on the board.
    
    @ivar dft_burn: Number of seconds flames last by default.
    """
    
    dft_burn = 1


    def __init__(self, reactor=reactor):
        self.fg_tiles = {}
        self.bombs = {}
        self.fires = {}
        self.pawns = set()
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
        call = self._reactor.callLater(fuse,
                                       self.detonateBomb, coord)
        self.bombs[coord] = (defer, call, size)
        return defer


    def detonateBomb(self, coord):
        """
        Detonate a bomb.
        
        @param coord: Tuple coordinate of bomb to detonate.
        """
        defer, call, size = self.bombs[coord]
        del self.bombs[coord]
        
        defer.callback(None)
        if call.active():
            call.cancel()
        
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
                if target in self.bombs:
                    directions.remove(d)
                if tile == SOFT:
                    directions.remove(d)
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
        This is currently not the case, but doesn't matter because
        all fires burn the same length.
        
        @param coord: Coordinate tuple to ignite
        
        @type burntime: int or float
        @param burntime: Seconds to keep burning.
        
        @return: L{Deferred} which fires when the fire is out.
        """
        if coord in self.fires:
            defer, call = self.fires[coord]
            call.reset(burntime)
        else:
            defer = Deferred()
            call = self._reactor.callLater(burntime, 
                                           self.stopFire, 
                                           coord)
            self.fires[coord] = (defer, call)
            self.fg_tiles[coord] = EMPTY
            if coord in self.bombs:
                self.detonateBomb(coord)
            for pawn in [x for x in self.pawns if x.loc==coord]:
                pawn.kill()
        return defer


    def insertPawn(self, coord, pawn):
        """
        Add a Pawn to the board.
        
        @param coord: Tuple coordinate to place the pawn
        @param pawn: L{Pawn} to insert.
        """
        pawn.board = self
        pawn.loc = coord
        self.pawns.add(pawn)
        self.fg_tiles[pawn.loc] = EMPTY
        directions = [
            (1,0),
            (-1,0),
            (0,1),
            (0,-1),
        ]
        for d in directions:
            target = (pawn.loc[0]+d[0], pawn.loc[1]+d[1])
            if target in self.fg_tiles:
                self.fg_tiles[target] = EMPTY


    def pawnMoved(self, pawn, new_loc):
        """
        A pawn has entered a new location
        """
        pawn.loc = new_loc
        if new_loc in self.fires:
            pawn.kill()


class Pawn:
    """
    I am a player (or NPC) on a L{Board}.  I walk around and put
    bombs down.
    """
    
    bombs = 1
    flame_size = 1
    fuse = 2.0
    alive = True
    board = None
    loc = None


    def __init__(self, name=None):
        self.name = name


    def kill(self):
        """
        Kill this pawn dead.
        """
        self.alive = False


    def dropBomb(self):
        """
        Drop a bomb on the C{board} at the current location.
        """
        if not self.alive:
            raise YoureDead("Dead people can't drop bombs")
        if self.bombs <= 0:
            raise IllegalMove("You're out of bombs")
        self.bombs -= 1
        d = self.board.dropBomb(self.loc, self.fuse, 
                                self.flame_size)
        def bombExploded(result, pawn):
            pawn.bombs += 1

        d.addCallback(bombExploded, self)


    def move(self, direction):
        """
        Move the pawn in a direction.
        
        Note: currently, pawns can move "infinitely" fast.  Later,
        speed will be added so that they can't.
        """
        if not self.alive:
            raise YoureDead("Dead peope can't move")
        delta = {
            'u': (0,-1),
            'd': (0,1),
            'l': (-1,0),
            'r': (1,0),
        }[direction]
        target = (self.loc[0]+delta[0], self.loc[1]+delta[1])
        try:
            tile = self.board.fgTile(target)
        except KeyError:
            raise IllegalMove("That would be off the board")
        if tile != EMPTY:
            raise IllegalMove("There's a brick there")
        if target in self.board.bombs:
            raise IllegalMove("There's a bomb there")
        self.board.pawnMoved(self, target)



