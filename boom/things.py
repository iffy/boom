from twisted.internet import defer, reactor

FIXEDBLOCK = 0
DESTRUCTABLE = 1
EMPTY = 2

class NotAllowed(Exception):
    pass


class Guy:

    speed = 0.5
    bombs = 1
    bomb_flare = 1
    bomb_fuse = 2.0
    dead = False
    board = None

    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return 'Guy(%r, %s)' % (self.name, self.dead)


class Board:
    
    def __init__(self):
        self.guys = {}
        self.tiles = {}
        self.listeners = []
        self.bombs = {}

    def generate(self, width, height):
        self.tiles = {}
        for y in xrange(height):
            for x in xrange(width):
                tile = EMPTY
                if x % 2 and y %2:
                    tile = FIXEDBLOCK
                self.tiles[(x,y)] = tile

    def addListener(self, listener):
        self.listeners.append(listener)

    def signal(self, event, *args):
        for listener in self.listeners:
            listener(event, args)

    def addGuy(self, guy, x, y):
        self.guys[guy] = (x,y)
        self.signal('born', guy, (x,y))
        self.tiles[(x,y)] = EMPTY

    def moveGuy(self, guy, direction):
        location = self.guys[guy]
        dst = None
        if direction == 'up':
            dst = location[0], location[1]-1
        elif direction == 'down':
            dst = location[0], location[1]+1
        elif direction == 'left':
            dst = location[0]-1, location[1]
        elif direction == 'right':
            dst = location[0]+1, location[1]
        try:
            tile = self.tiles[dst]
        except KeyError:
            raise NotAllowed("Can't move there: edge of world")
        if tile in [FIXEDBLOCK, DESTRUCTABLE]:
            raise NotAllowed("Can't move there: wall")
        if dst in self.bombs:
            raise NotAllowed("Can't move there: bomb")
        self.guys[guy] = dst
        self.signal('move', guy, dst)

    def placeBomb(self, guy):
        if not guy.bombs:
            raise NotAllowed("Fresh out")
        if guy.dead:
            raise NotAllowed("you're dead")
        location = self.guys[guy]
        if location in self.bombs:
            raise NotAllowed("There's a bomb there")
        
        # take a bomb away
        guy.bombs -= 1
        self.bombs[location] = (guy, guy.bomb_flare)
        self.signal('bomb', guy, location)
        reactor.callLater(guy.bomb_fuse, self.explode, location)

    def explode(self, location):
        if location not in self.bombs:
            # already exploded
            return
        
        guy, flare = self.bombs[location]
        del self.bombs[location]
        
        # give a bomb back
        guy.bombs += 1
        
        fires = []
        
        deltas = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0),
        ]
        
        self.igniteTile(location)
        for delta in deltas:
            for i in xrange(1, flare+1):
                delta = location[0]+delta[0]*i, location[1]+delta[1]*i
                try:
                    tile = self.tiles[delta]
                except KeyError:
                    break
                if tile == FIXEDBLOCK:
                    break
                elif tile == DESTRUCTABLE:
                    self.igniteTile(delta)
                    break
                else:
                    self.igniteTile(delta)

    def igniteTile(self, location):
        self.signal('fire', location)
        tile = self.tiles[location]
        if tile == DESTRUCTABLE:
            self.tiles[location] = EMPTY
            self.signal('tilechange', location, EMPTY)
            return
        
        for guy,v in self.guys.items():
            if v == location:
                self.killGuy(guy)
        
        if location in self.bombs:
            self.explode(location)

    def killGuy(self, guy):
        if not guy.dead:
            guy.dead = True
            self.signal('dead', guy)            
        


if __name__ == '__main__':
    def printer(signal, args):
        print signal, args    
    b = Board()
    b.addListener(printer)
    b.generate(3, 3)
    print b.tiles
    
    guy = Guy('bob')
    b.addGuy(guy, 0, 0)
    b.placeBomb(guy)
    b.moveGuy(guy, 'right')
    b.moveGuy(guy, 'right')
    
    g2 = Guy('joe')
    b.addGuy(g2, 0, 1)
    b.placeBomb(g2)
    
    reactor.callLater(4, reactor.stop)
    reactor.run()
    
    
