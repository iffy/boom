from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock

from boom.game import Bomb, Board, EMPTY, HARD, SOFT


class BombTest(TestCase):

    timeout = 2

    def test_init(self):
        bomb = Bomb(3, 4)
        self.assertEqual(bomb.fuse, 3)
        self.assertEqual(bomb.size, 4)

    def test_ignite(self):
        bomb = Bomb(1, 4)
        d = bomb.ignite()
        def check(result):
            self.assertEqual(result, bomb)
        return d.addCallback(check)


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


    def test_bomb(self):
        """
        You can place a bomb, and get a Deferred back that is called
        when the bomb goes off.
        """
        clock = Clock()
        board = Board(reactor=clock)
        board.generate(3,3)
        d = board.dropBomb((0,0), 10, 1)
        clock.advance(9)
        self.assertEqual(d.called, False, "No explosiong yet")
        clock.advance(1)
        self.assertEqual(d.called, True, "Now that the time has "
                         "elapsed, the bomb should have gone off")




