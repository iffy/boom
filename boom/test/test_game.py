from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock

from boom.game import Board, EMPTY, HARD, SOFT


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
                actual = board.fgTile((c,r))
                self.assertEqual(actual, tile, "Expected foreground"
                                 "tile at %s,%s to be %s, not %s"%(
                                 c,r,tile,actual))


    def test_dropBomb(self):
        """
        You can place a bomb, and get a Deferred back that is called
        when the bomb goes off.
        """
        clock = Clock()
        board = Board(reactor=clock)
        board.generate(1,1)
        
        d = board.dropBomb((0,0), 10, 1)
        self.assertTrue(board.bombs[(0,0)], "bomb is on the board")
        
        clock.advance(9)
        self.assertEqual(d.called, False, "No explosion yet")
        clock.advance(1)
        self.assertEqual(d.called, True, "Now that the time has "
                         "elapsed, the bomb should have gone off")
        self.assertTrue((0,0) not in board.bombs)


    def expectFires(self, board, expected):
        """
        Test that a C{board} has the C{expected} fires burning.
        
        @param board: L{Board}.
        @param expected: List of tuple coordinates of expected
            fires.
        """        
        expected = set(expected)
        actual = set(board.fires)
        
        missing = expected - actual
        extra = actual - expected
        self.assertEqual(extra, set(), "There are some fires "
                         "in the listed, unexpected tiles")
        self.assertEqual(missing, set(), "Expected fires to be "
                         "in these tiles, but they weren't")


    def test_dropBomb_startFire_SOFT(self):
        """
        Bombs should start fires in all SOFT spaces in the 
        area around the bomb.
        """
        clock = Clock()
        board = Board(reactor=clock)
        board.generate(5,5)
        board.dft_burn = 29
        
        d = board.dropBomb((2,2), 1, 1)
        clock.advance(1)

        self.expectFires(board, [
            (2,2),
            (2,1),
            (2,3),
            (1,2),
            (3,2),
        ])


    def test_dropBomb_HARD_adjacent(self):
        """
        If a HARD tile is adjacent to a bomb, no fire should
        be lit on the HARD tile
        """
        


    def test_startFire(self):
        """
        You can start a fire on a tile and get a Deferred back that
        fires when the fire is gone.
        """
        clock = Clock()
        board = Board(reactor=clock)
        board.generate(1,1)
        
        d = board.startFire((0,0), 3)
        self.assertTrue((0,0) in board.fires)
        self.assertEqual(board.fgTile((0,0)), EMPTY, "Should clear"
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
        clock = Clock()
        board = Board(reactor=clock)
        board.generate(1,1)
        
        d = board.startFire((0,0), 3)
        self.assertTrue((0,0) in board.fires)
        
        clock.advance(2)
        d2 = board.startFire((0,0), 5)
        
        clock.advance(2)
        self.assertEqual(d.called, False, "Should still burn")
        self.assertEqual(d2.called, False, "Should still burn")
        
        clock.advance(4)
        self.assertEqual(d.called, True, "Should be done")
        self.assertEqual(d2.called, True, "Burninate")



