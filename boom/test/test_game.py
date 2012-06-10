from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock

from boom.game import (Board, EMPTY, HARD, SOFT, Pawn, YoureDead,
                       IllegalMove)



def bnc():
    """
    Get a L{Board} with a C{Clock} for a reactor.
    
    @return: Tuple of L{Board}, C{Clock} instances.
    """
    clock = Clock()
    board = Board(reactor=clock)
    return board, clock


def map2coord(visual):
    """
    Convert a 'visual' representation of bits into coordinates...
    err... so this::
    
        [' x ','   ','x  ']
    
    Becomes this:
    
        [(1,0), (0,2)]

    @rtype: list
    """
    ret = []
    for i,line in enumerate(visual):
        for j,char in enumerate(line):
            if char != ' ':
                ret.append((j,i))
    return ret


def coord2map(coords):
    """
    The inverse of L{map2coord}.
    """
    ret = []
    width = max([x[0] for x in coords] + [0])
    height = max([x[1] for x in coords] + [0])
    for y in xrange(height+1):
        row = ''
        for x in xrange(width+1):
            coord = (x,y)
            if coord in coords:
                row += 'x'
            else:
                row += ' '
        ret.append(row)
    return ret



class BoardTest(TestCase):

    timeout = 2


    def test_reactor(self):
        """
        You can initialize the Board with any reactor you want
        (useful for testing).
        """
        board = Board(reactor='foo')
        self.assertEqual(board._reactor, 'foo')


    def test_generate(self):
        """
        You should be able to generate a standard board of any size,
        where there's indestructable bricks in a grid like this:
        """
        board = Board()
        board.generate(5, 5)
        expected = [
            [SOFT, SOFT, SOFT, SOFT, SOFT],
            [SOFT, HARD, SOFT, HARD, SOFT],
            [SOFT, SOFT, SOFT, SOFT, SOFT],
            [SOFT, HARD, SOFT, HARD, SOFT],
            [SOFT, SOFT, SOFT, SOFT, SOFT],
        ]
        for r,row in enumerate(expected):
            for c,tile in enumerate(row):
                actual = board.fg_tiles[(c,r)]
                self.assertEqual(actual, tile, "Expected foreground"
                                 "tile at %s,%s to be %s, not %s"%(
                                 c,r,tile,actual))


    def test_dropBomb(self):
        """
        You can place a bomb, and get a Deferred back that is called
        when the bomb goes off.
        """
        board, clock = bnc()
        board.generate(1,1)
        
        d = board.dropBomb((0,0), 10, 1)
        self.assertTrue(board.bombs[(0,0)], "bomb is on the board")
        
        clock.advance(9)
        self.assertEqual(d.called, False, "No explosion yet")
        clock.advance(1)
        self.assertEqual(d.called, True, "Now that the time has "
                         "elapsed, the bomb should have gone off")
        self.assertTrue((0,0) not in board.bombs)


    def assertCoordsEqual(self, a, b, msg=''):
        """
        Assert that two sets of coordinates are the same, and
        display a visual representation of them if they are not.
        """
        self.assertEqual(set(a), set(b), '%s:\n%s\n--- not ---\n%s' % (
            msg or 'Coordinate maps not equal',
            '\n'.join(coord2map(a)),
            '\n'.join(coord2map(b)),
        ))


    def expectFires(self, board, expected):
        """
        Test that a C{board} has the C{expected} fires burning.
        
        @param board: L{Board}.
        @param expected: List of strings with X showing where
            fire ought to be.  Like this for a 3x3::
            
                ' XX',
                '  X',
                '   ',

        """
        expected_coords = set()
        for i,line in enumerate(expected):
            for j,char in enumerate(line):
                if char.lower() == 'x':
                    expected_coords.add((j,i))
        expected = set(map2coord(expected))
        actual = set(board.fires)
        
        missing = expected - actual
        extra = actual - expected
        self.assertEqual(extra, set(), "There are some unexpected "
                        "fires in the listed tiles")
        self.assertEqual(missing, set(), "Expected fires to be "
                         "in these tiles, but they weren't")


    def test_fallout_single_SOFT(self):
        """
        Bombs should start fires in all SOFT spaces in the 
        area around the bomb.
        """
        board, clock = bnc()
        board.generate(3,3)
        board.fg_tiles.update({
            (1,1): EMPTY,
        })
        board.dft_burn = 29
        
        d = board.dropBomb((1,1), 1, 1)
        clock.advance(1)

        self.expectFires(board, [
            ' x ',
            'xxx',
            ' x ',
        ])


    def test_fallout_single_HARD(self):
        """
        If a HARD tile is adjacent to a bomb, no fire should
        be lit on the HARD tile
        """
        board, clock = bnc()
        board.generate(3,3)
        board.fg_tiles.update({
            (1,0): HARD,
            (0,1): HARD,
            (1,2): HARD,
            (2,1): HARD,
            (1,1): EMPTY,
        })
        
        board.dropBomb((1,1), 1, 1)
        clock.advance(1)
        self.expectFires(board, [
            '   ',
            ' x ',
            '   ',
        ])


    def test_fallout_edges(self):
        """
        Fires can't happen outside the board
        """
        board, clock = bnc()
        board.generate(5,5)
        board.fg_tiles.update({
            (0,0): EMPTY,
            (4,4): EMPTY,
            (0,4): EMPTY,
            (4,0): EMPTY,
        })
        board.dropBomb((0,0), 1, 1)
        board.dropBomb((4,0), 1, 1)
        board.dropBomb((0,4), 1, 1)
        board.dropBomb((4,4), 1, 1)
        clock.advance(1)
        self.expectFires(board, [
            'xx xx',
            'x   x',
            '     ',
            'x   x',
            'xx xx',
        ])


    def test_fallout_obstruction(self):
        """
        If a larger bomb is obstructed by a HARD/SOFT tile, it 
        should not continue beyond the tile.
        """
        board, clock = bnc()
        board.generate(5,5)
        board.fg_tiles.update({
            (2,1): EMPTY,
        })
        board.dropBomb((2,1), 1, 4)
        clock.advance(1)
        self.expectFires(board, [
            '  X  ',
            '  X  ',
            '  X  ',
            '     ',
            '     ',
        ])


    def test_bomb_light_bomb(self):
        """
        A bomb can ignite another bomb prematurely.
        """
        board, clock = bnc()
        board.generate(3,3)
        board.fg_tiles.update({
            (0,0): EMPTY,
            (1,0): EMPTY,
        })
        board.dropBomb((0,0), 10, 1)
        board.dropBomb((1,0), 1, 1)
        clock.advance(1)
        self.expectFires(board, [
            'xxx',
            'x  ',
            '   ',
        ])
        self.assertEqual(board.bombs, {}, "The bomb should have "
                         "exploded")
        clock.advance(10)


    def test_fire_smallBomb_bigBomb(self):
        """
        A small bomb will obstruct a big bomb's explosion fr
        """
        board, clock = bnc()
        board.generate(5,5)
        empties = map2coord([
            'xxxxx',
            '  x  ',
            '  x  ',
            '  x  ',
            '  x  ',
        ])
        for empty in empties:
            board.fg_tiles[empty] = EMPTY
        board.dropBomb((2,0), 1, 10)
        board.dropBomb((2,1), 5, 1)
        clock.advance(1)
        self.expectFires(board, [
            'xxxxx',
            '  x  ',
            '  x  ',
            '     ',
            '     ',
        ])


    def test_startFire(self):
        """
        You can start a fire on a tile and get a Deferred back that
        fires when the fire is gone.
        """
        board, clock = bnc()
        board.generate(1,1)
        
        d = board.startFire((0,0), 3)
        self.assertTrue((0,0) in board.fires)
        self.assertEqual(board.fg_tiles[(0,0)], EMPTY, "Should clear"
                         " out the tile")
        
        clock.advance(2)
        self.assertEqual(d.called, False, "Still burning")
        
        clock.advance(1)
        self.assertEqual(d.called, True, "Fire is out")
        self.assertTrue((0,0) not in board.fires)


    def test_startFire_overlap(self):
        """
        A fire will continue burning if you start it again before
        it's done.
        """
        board, clock = bnc()
        board.generate(1,1)
        
        d = board.startFire((0,0), 3)
        self.assertTrue((0,0) in board.fires)
        
        clock.advance(2)
        d2 = board.startFire((0,0), 5)
        
        clock.advance(1)
        self.assertEqual(d.called, False, "Should still burn")
        self.assertEqual(d2.called, False, "Should still burn")
        
        clock.advance(4)
        self.assertEqual(d.called, True, "Should be done")
        self.assertEqual(d2.called, True, "Burninate")


    def test_startFire_igniteBomb(self):
        """
        A fire will ignite a bomb prematurely
        """
        board, clock = bnc()
        board.generate(1,1)
        
        d = board.dropBomb((0,0), 10, 1)
        d2 = board.startFire((0,0), 1)
        clock.advance(1)
        self.assertEqual(board.bombs, {}, "Bomb should be gone")
        self.assertTrue(d.called, "Should have ignited the bomb")
        
        # make sure there's no errors when the original explosion
        # should happen
        clock.advance(10)


    def test_insertPawn(self):
        """
        You can put a pawn on the board (and into the game)
        """
        pawn = Pawn()
        board = Board()
        board.generate(1,1)
        board.insertPawn((0,0), pawn)
        self.assertEqual(pawn.board, board, "Pawn should know "
                         "he's on the board.")
        self.assertEqual(pawn.loc, (0,0), "Pawn should know where"
                         " he is on the board")
        
        self.assertTrue(pawn in board.pawns, "Board should know "
                        "about the Pawn")


    def test_insertPawn_makeRoom(self):
        """
        When pawns are inserted, a space should be made for them.
        For now, make a space on all sides.  Later, this could
        change.
        """
        board = Board()
        board.generate(5,5)
        locs = map2coord([
            'x   x',
            '     ',
            '  x  ',
            '     ',
            'x   x',
        ])
        pawns = []
        for loc in locs:
            pawns.append(Pawn())
            board.insertPawn(loc, pawns[-1])
        
        expected_empty = map2coord([
            'xx xx',
            'x x x',
            ' xxx ',
            'x x x',
            'xx xx',
        ])
        actual_empty = set()
        for k,v in board.fg_tiles.items():
            if v == EMPTY:
                actual_empty.add(k)
        
        self.assertCoordsEqual(expected_empty, actual_empty,
                               "Expected empty tiles to be thus")
        

    def test_fire_kills_pawn(self):
        """
        If a Pawn is present when a fire starts, the Pawn dies.
        """
        pawn = Pawn()
        board, clock = bnc()
        board.insertPawn((0,0), pawn)
        board.startFire((0,0), 1)
        self.assertFalse(pawn.alive, "Pawn should be dead now")


    def test_pawnMoved(self):
        """
        When a pawn is moved, the board knows.
        """
        pawn = Pawn()
        board, clock = bnc()
        board.generate(3,3)
        board.insertPawn((0,0), pawn)
        board.pawnMoved(pawn, (1,0))
        self.assertEqual(pawn.loc, (1,0), "Should know that it"
                         " moved")


    def test_pawnMoved_fire(self):
        """
        If a pawn moves into fire, they die
        """
        pawn = Pawn()
        board, clock = bnc()
        board.generate(3,3)
        board.insertPawn((0,0), pawn)
        board.startFire((1,0), 1)
        board.pawnMoved(pawn, (1,0))
        self.assertEqual(pawn.alive, False, "Pawn should die")
        


class PawnTest(TestCase):


    def test_attrs(self):
        """
        A pawn should have these attributes by default
        """
        pawn = Pawn('john')
        self.assertEqual(pawn.name, 'john')
        self.assertEqual(pawn.bombs, 1, "Should have one bomb")
        self.assertEqual(pawn.flame_size, 1)
        self.assertEqual(pawn.fuse, 2.0)
        self.assertEqual(pawn.alive, True)
        self.assertEqual(pawn.board, None)
        self.assertEqual(pawn.loc, None)
        

    def test_kill(self):
        """
        You can kill pawns
        """
        pawn = Pawn()
        pawn.kill()
        self.assertEqual(pawn.alive, False)


    def test_dropBomb(self):
        """
        You can drop bombs on the board, which uses up one of the
        bombs until it explodes.
        """
        board, clock = bnc()
        board.generate(5,5)
        pawn = Pawn()
        pawn.fuse = 3
        
        board.insertPawn((0,0), pawn)
        pawn.dropBomb()
        self.assertEqual(pawn.bombs, 0, "Should use up a bomb")
        self.assertTrue((0,0) in board.bombs, "Bomb should be on"
                        " the board")
        clock.advance(3)
        self.assertEqual(pawn.bombs, 1, "Should get the bomb back")
        self.assertFalse((0,0) in board.bombs)


    def test_dropBomb_dead(self):
        """
        You can't drop bombs if you're dead
        """
        board, clock = bnc()
        board.generate(5,5)
        
        pawn = Pawn()
        board.insertPawn((0,0), pawn)
        pawn.kill()
        self.assertRaises(YoureDead, pawn.dropBomb)
        self.assertTrue((0,0) not in board.bombs)


    def test_dropBomb_havenone(self):
        """
        You can't drop bombs if you don't have any
        """
        pawn = Pawn()
        pawn.bombs = 0
        self.assertRaises(IllegalMove, pawn.dropBomb)


    def test_move(self):
        """
        You can move it up,down,left or right, and pawnMoved will
        be called after each move.
        """
        board, clock = bnc()
        board.generate(5,5)
        board.fg_tiles[(1,1)] = EMPTY

        pawn = Pawn()
        board.insertPawn((0,0), pawn)
        
        # fake out pawnMoved
        called = []
        real_pawnMoved = board.pawnMoved
        def fake_pawnMoved(*args):
            called.append(args)
            return real_pawnMoved(*args)
        board.pawnMoved = fake_pawnMoved
        
        pawn.move('r')
        self.assertEqual(called[0], (pawn, (1,0)), "Should have "
                         "called pawnMoved")

        called.pop()
        pawn.move('d')
        self.assertEqual(called[0], (pawn, (1,1)))
        
        called.pop()
        pawn.move('l')
        self.assertEqual(called[0], (pawn, (0,1)))
        
        called.pop()
        pawn.move('u')
        self.assertEqual(called[0], (pawn, (0,0)))


    def test_illegal_moves(self):
        """
        Pawns can only move into EMPTY tiles.  Can't move into
        bombs, HARD, SOFT or off the board.
        """
        board, clock = bnc()
        board.generate(3,3)
        pawn = Pawn()
        board.insertPawn((0,0), pawn)
        
        # off the board
        self.assertRaises(IllegalMove, pawn.move, 'l')
        self.assertRaises(IllegalMove, pawn.move, 'u')
        
        pawn.move('d')
        self.assertEqual(pawn.loc, (0,1))
        
        # HARD
        self.assertRaises(IllegalMove, pawn.move, 'r')
        # SOFT
        self.assertRaises(IllegalMove, pawn.move, 'd')
        
        pawn.dropBomb()
        pawn.move('u')
        
        # on bomb
        self.assertRaises(IllegalMove, pawn.move, 'd')


    def test_move_dead(self):
        """
        You can't move when dead
        """
        pawn = Pawn()
        pawn.kill()
        self.assertRaises(YoureDead, pawn.move, 'u')


